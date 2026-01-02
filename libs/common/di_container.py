# ============================================================
# Common DI Container Utilities
# ============================================================
# This module provides generic dependency injection utilities
# that can be shared between batch and webapi applications.
# ============================================================

import inspect
import sys
from typing import Any, Dict, Type, get_args, get_origin, get_type_hints

from dependency_injector import containers, providers

from common.di_registry import DIRegistry
from common.interfaces import (
    IDatabaseConnection,
    IDependencyProvider,
    IAppConfig,
)
from infrastructure_layer.session_factory import SessionFactory
from sqlalchemy.orm import Session


# ============================================================
# Type introspection utilities
# ============================================================

def _resolve_type_hints(func: Any) -> Dict[str, Any]:
    """
    Resolve constructor type hints, supporting:
    - forward references
    - string annotations
    - DIRegistry interfaces
    
    Args:
        func: Function or method to introspect
        
    Returns:
        Dictionary mapping parameter names to their types
    """
    # Handle wrapper descriptors and built-in types that don't have __module__
    if not hasattr(func, "__module__"):
        # For wrapper descriptors (like built-in types), return empty hints
        # These types typically don't need dependency injection
        return {}
    
    module = sys.modules.get(func.__module__)
    namespace: Dict[str, Any] = dict(module.__dict__) if module else {}

    # Add DIRegistry interfaces to namespace for forward reference resolution
    namespace.update({iface.__name__: iface for iface in DIRegistry._registry.keys()})
    
    # Add core interfaces to namespace
    namespace.update(
        {
            "IAppConfig": IAppConfig,
            "IDatabaseConnection": IDatabaseConnection,
            "SessionFactory": SessionFactory,
            "Session": Session,
        }
    )

    try:
        return get_type_hints(func, globalns=namespace)
    except (NameError, TypeError, AttributeError):
        # Fallback: try to get hints from signature
        try:
            hints: Dict[str, Any] = {}
            sig = inspect.signature(func)
            for name, param in sig.parameters.items():
                if name == "self" or param.annotation is inspect.Parameter.empty:
                    continue
                hints[name] = param.annotation
            return hints
        except (ValueError, TypeError, AttributeError):
            # If signature inspection also fails, return empty dict
            return {}


# ============================================================
# Provider graph construction
# ============================================================

_PRIMITIVE_TYPES = (int, float, str, bool, bytes, type(None))


def _create_provider(
    interface: Type[Any],
    impl: Type[Any],
    providers_map: Dict[Type[Any], providers.Provider],
    visited: set[Type[Any]],
) -> providers.Factory:
    """
    Recursively create a provider for an interface/implementation pair.
    
    This function:
    1. Detects circular dependencies
    2. Resolves constructor dependencies
    3. Creates providers for dependencies recursively
    4. Returns a Factory provider for the implementation
    
    Args:
        interface: The interface type to register
        impl: The implementation class
        providers_map: Map of already-created providers (for dependency resolution)
        visited: Set of interfaces currently being processed (for cycle detection)
        
    Returns:
        Factory provider for the implementation
        
    Raises:
        ValueError: If circular dependency detected or unknown dependency found
    """
    # Detect circular dependencies
    if interface in visited:
        raise ValueError(f"Circular dependency detected: {interface.__name__}")

    # Return existing provider if already created
    if interface in providers_map:
        return providers_map[interface]

    # Mark as visited to detect cycles
    visited.add(interface)

    # Get type hints from constructor
    hints = _resolve_type_hints(impl.__init__)
    sig = inspect.signature(impl.__init__)
    deps: Dict[str, providers.Provider] = {}

    # Process each constructor parameter
    for name, param_type in hints.items():
        if name in ("self", "return"):
            continue

        param = sig.parameters.get(name)
        
        # Skip parameters with default values
        if param and param.default is not inspect.Parameter.empty:
            continue

        # Skip primitive types (they don't need DI)
        if (
            param_type in _PRIMITIVE_TYPES
            or isinstance(param_type, type)
            and issubclass(param_type, _PRIMITIVE_TYPES)
        ):
            continue

        # Handle generic types (e.g., List[str] -> str)
        if get_origin(param_type):
            args = get_args(param_type)
            if args:
                param_type = args[0]

        # Resolve dependency provider
        if param_type in providers_map:
            # Use existing provider
            deps[name] = providers_map[param_type]
        elif DIRegistry.is_registered(param_type):
            # Recursively create provider for dependency
            dep_provider = _create_provider(
                param_type,
                DIRegistry.get(param_type),
                providers_map,
                visited,
            )
            providers_map[param_type] = dep_provider
            deps[name] = dep_provider
        else:
            raise ValueError(
                f"Unknown dependency {param_type.__name__} "
                f"for {impl.__name__}.{name}"
            )

    # Create and register the provider
    provider = providers.Factory(impl, **deps)
    providers_map[interface] = provider
    visited.remove(interface)
    return provider


# ============================================================
# Naming utilities
# ============================================================

def _normalize_attr_name(tp: Type[Any]) -> str:
    """
    Convert interface/class name to container attribute name.
    
    Examples:
        IAppConfig -> app_config
        IDatabaseConnection -> db_connection
        IWalnutAL -> walnut_al
        
    Args:
        tp: Type to convert
        
    Returns:
        Normalized attribute name
    """
    name = tp.__name__.lower()
    if name.startswith("i"):
        name = name[1:]

    return (
        name.replace("appconfig", "app_config")
        .replace("databaseconnection", "db_connection")
        .replace("walnutal", "walnut_al")
    )


# ============================================================
# Runtime resolution adapter (infrastructure boundary)
# ============================================================

def _container_resolve(container: containers.DeclarativeContainer, dependency_type: Type[Any]) -> Any:
    """
    Resolve a dependency type to an instance using the container.
    
    Resolution order:
    1. Check if container has a provider for the type
    2. Fall back to DIRegistry if registered
    3. Finally try to instantiate the type directly (for simple cases)
    
    Args:
        container: The DI container instance
        dependency_type: The type to resolve
        
    Returns:
        An instance of the requested type
    """
    # Try to find provider on container
    attr_name = _normalize_attr_name(dependency_type)
    if hasattr(container, attr_name):
        provider = getattr(container, attr_name)
        return provider() if callable(provider) else provider

    # Try DIRegistry
    if DIRegistry.is_registered(dependency_type):
        impl = DIRegistry.get(dependency_type)
        hints = _resolve_type_hints(impl.__init__)
        deps = {
            name: _container_resolve(container, param_type)
            for name, param_type in hints.items()
            if name not in ("self", "return")
        }
        return impl(**deps)

    # Last resort: try to instantiate directly
    hints = _resolve_type_hints(dependency_type.__init__)
    deps = {
        name: _container_resolve(container, param_type)
        for name, param_type in hints.items()
        if name not in ("self", "return")
    }
    return dependency_type(**deps)


# ============================================================
# Dependency Provider Adapter
# ============================================================

class DependencyProviderWrapper(IDependencyProvider):
    """
    Adapter so application layer does not depend on
    dependency_injector or container internals.
    
    This is a generic adapter that can be used by both
    batch and webapi applications.
    """

    def __init__(self, container: containers.DeclarativeContainer) -> None:
        self._container = container

    def resolve(self, dependency_type: Type[Any]) -> Any:
        """Resolve a dependency by type."""
        return _container_resolve(self._container, dependency_type)
