# src/common/di_container.py
"""
Dependency Injection Container using dependency-injector framework.

HOW IT WORKS:
1. Register interface-to-implementation mappings in di_registry.py
2. That's it! Providers are automatically created and dependencies are auto-resolved
3. Only manually wire providers for special cases (like db_connection that needs app_config)

When you add a new interface dependency to a class constructor:
- Just register the interface in di_registry.py
- Done! The container automatically creates the provider and resolves dependencies
"""
import inspect
from dependency_injector import containers, providers
from pathlib import Path
import psycopg2
from typing import get_type_hints, get_origin, get_args, Dict, Type, Any

from src.common.app_config import AppConfig
from src.common.interfaces import IAppConfig, IDatabaseConnection
from src.common.di_registry import DIRegistry
from src.business_layers.walnut_bl import IWalnutBL, WalnutBL
from src.domain_layers.services.embedding_service import IImageEmbeddingService
from src.data_access_layers.db_readers import (
    IWalnutReader,
    IWalnutImageReader,
    IWalnutImageEmbeddingReader,
)


def create_app_config(config_path: Path) -> IAppConfig:
    """Factory function to create AppConfig from YAML path."""
    return AppConfig.load_from_yaml(config_path)


def create_db_connection(app_config: IAppConfig) -> IDatabaseConnection:
    """Factory function to create a database connection from AppConfig."""
    return psycopg2.connect(
        host=app_config.database.host,
        port=app_config.database.port,
        database=app_config.database.database,
        user=app_config.database.user,
        password=app_config.database.password,
    )


def create_auto_provider(
    interface: Type[Any],
    implementation_class: Type[Any],
    all_providers: Dict[Type[Any], providers.Provider],
    visited: set,
) -> providers.Provider:
    """
    Recursively create a provider for an interface, automatically resolving all dependencies.
    
    This function:
    1. Inspects the implementation class constructor
    2. Finds all dependencies (from type hints)
    3. Recursively creates providers for dependencies
    4. Creates a Factory provider with all dependencies wired
    
    Args:
        interface: The interface type
        implementation_class: The concrete implementation class
        all_providers: Dict of already-created providers (to avoid cycles and reuse)
        visited: Set of interfaces being processed (to detect cycles)
    
    Returns:
        A Factory provider with all dependencies automatically resolved
    """
    # Avoid cycles
    if interface in visited:
        raise ValueError(f"Circular dependency detected involving {interface.__name__}")
    
    # Return existing provider if already created
    if interface in all_providers:
        return all_providers[interface]
    
    visited.add(interface)
    
    # Get constructor signature and type hints
    init_signature = inspect.signature(implementation_class.__init__)
    type_hints = get_type_hints(implementation_class.__init__)
    
    # Build dependency mapping
    dependencies = {}
    for param_name, param in init_signature.parameters.items():
        if param_name == "self":
            continue
        
        param_type = type_hints.get(param_name)
        if param_type is None:
            continue
        
        # Handle Optional types
        origin = get_origin(param_type)
        if origin is not None:
            args = get_args(param_type)
            if args:
                param_type = args[0]
        
        # Resolve dependency
        if param_type in all_providers:
            # Use existing provider
            dependencies[param_name] = all_providers[param_type]
        elif DIRegistry.is_registered(param_type):
            # Recursively create provider for this dependency
            dep_impl = DIRegistry.get(param_type)
            dep_provider = create_auto_provider(
                param_type, dep_impl, all_providers, visited.copy()
            )
            all_providers[param_type] = dep_provider
            dependencies[param_name] = dep_provider
        else:
            raise ValueError(
                f"Unknown dependency type {param_type.__name__} for parameter '{param_name}' "
                f"in {implementation_class.__name__}. Register it in di_registry.py first."
            )
    
    # Create factory provider
    provider = providers.Factory(implementation_class, **dependencies)
    all_providers[interface] = provider
    visited.remove(interface)
    
    return provider


def create_auto_factory(implementation_class, all_providers):
    """
    Create a factory provider that automatically resolves dependencies.
    
    Usage:
        walnut_bl = create_auto_factory(WalnutBL, container._all_providers)
    
    Args:
        implementation_class: The concrete class to instantiate
        all_providers: Dict mapping interface types to their providers
    
    Returns:
        A Factory provider with automatically resolved dependencies
    """
    # Get constructor signature and type hints
    init_signature = inspect.signature(implementation_class.__init__)
    type_hints = get_type_hints(implementation_class.__init__)
    
    # Build dependency mapping
    dependencies = {}
    for param_name, param in init_signature.parameters.items():
        if param_name == "self":
            continue
        
        param_type = type_hints.get(param_name)
        if param_type is None:
            continue
        
        # Handle Optional types
        origin = get_origin(param_type)
        if origin is not None:
            args = get_args(param_type)
            if args:
                param_type = args[0]
        
        # Find the provider for this type
        if param_type in all_providers:
            dependencies[param_name] = all_providers[param_type]
        else:
            raise ValueError(
                f"Unknown dependency type {param_type.__name__} for parameter '{param_name}'. "
                f"Register it in di_registry.py first."
            )
    
    # Create factory with auto-resolved dependencies
    return providers.Factory(implementation_class, **dependencies)


def _interface_to_attr_name(interface: Type[Any]) -> str:
    """Convert interface name to attribute name."""
    name = interface.__name__
    # Remove 'I' prefix if present
    if name.startswith("I") and len(name) > 1:
        name = name[1:]
    # Convert CamelCase to snake_case
    import re
    name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
    # Handle special cases
    if name == "app_config":
        return "app_config"
    elif name == "database_connection":
        return "db_connection"
    return name


# Build all providers automatically from registry
# This happens at module load time
_all_providers: Dict[Type[Any], providers.Provider] = {}


class Container(containers.DeclarativeContainer):
    """Dependency Injection Container for the application."""

    # Configuration path - will be set from YAML file
    config_path = providers.Configuration()

    # Special providers that need manual setup (not in registry)
    # AppConfig factory - loads from YAML
    app_config = providers.Singleton(
        create_app_config,
        config_path=config_path,
    )

    # Database connection factory (special case - needs app_config)
    db_connection = providers.Singleton(
        create_db_connection,
        app_config=app_config,
    )


# Initialize providers after Container class is defined
# We use a function that gets called to set up providers
def _initialize_providers():
    """Initialize all providers from registry after Container class is defined."""
    # Add special providers to dict
    _all_providers[IAppConfig] = Container.app_config
    _all_providers[IDatabaseConnection] = Container.db_connection

    # Automatically create providers for all registered interfaces
    # This runs at module import time - all providers are created automatically!
    for interface in DIRegistry._registry.keys():
        if interface not in _all_providers:
            implementation = DIRegistry.get(interface)
            provider = create_auto_provider(
                interface, implementation, _all_providers, set()
            )
            _all_providers[interface] = provider
            # Add as class attribute so it's accessible
            attr_name = _interface_to_attr_name(interface)
            setattr(Container, attr_name, provider)

    # Create providers for business logic classes
    # Just add your class here - dependencies are auto-resolved!
    Container.walnut_bl = create_auto_factory(WalnutBL, _all_providers)


# Initialize providers after Container is defined
_initialize_providers()
