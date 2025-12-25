# src/common/di_container.py
"""
Dependency Injection Container - Automatically resolves dependencies from registry.

HOW IT WORKS:
1. Register interface-to-implementation in di_registry.py
2. Providers are auto-created with dependencies resolved
3. Just use: container.walnut_bl() - all dependencies injected!
"""
import inspect
import sys
from dependency_injector import containers, providers
from pathlib import Path
import psycopg2
from typing import get_type_hints, get_origin, get_args, Dict, Type, Any

from src.common.app_config import AppConfig
from src.common.interfaces import IAppConfig, IDatabaseConnection
from src.common.di_registry import DIRegistry
from src.business_layers.walnut_bl import WalnutBL
# Import all interfaces to resolve forward references
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


def _get_type_hints_safe(func):
    """Get type hints with proper namespace for forward references."""
    # Get module namespace
    module = sys.modules.get(func.__module__) if hasattr(func, '__module__') else None
    namespace = module.__dict__ if module else {}
    
    # Add all registered interfaces to namespace
    for interface in DIRegistry._registry.keys():
        namespace[interface.__name__] = interface
    
    # Add common interfaces
    namespace.update({
        'IAppConfig': IAppConfig,
        'IDatabaseConnection': IDatabaseConnection,
        'IWalnutImageEmbeddingReader': IWalnutImageEmbeddingReader,
        'IWalnutImageReader': IWalnutImageReader,
        'IWalnutReader': IWalnutReader,
    })
    
    try:
        return get_type_hints(func, globalns=namespace)
    except (NameError, TypeError):
        # Fallback: parse annotations manually
        hints = {}
        for param_name, param in inspect.signature(func).parameters.items():
            if param_name != "self" and param.annotation != inspect.Parameter.empty:
                ann = param.annotation
                if isinstance(ann, str):
                    class_name = ann.strip('"\'')
                    if class_name in namespace:
                        hints[param_name] = namespace[class_name]
                else:
                    hints[param_name] = ann
        return hints


def create_auto_provider(
    interface: Type[Any],
    implementation_class: Type[Any],
    all_providers: Dict[Type[Any], providers.Provider],
    visited: set,
) -> providers.Provider:
    """Create a provider with auto-resolved dependencies."""
    if interface in visited:
        raise ValueError(f"Circular dependency: {interface.__name__}")
    if interface in all_providers:
        return all_providers[interface]
    
    visited.add(interface)
    
    # Get type hints (exclude return type)
    type_hints = _get_type_hints_safe(implementation_class.__init__)
    
    # Resolve dependencies
    dependencies = {}
    for param_name, param_type in type_hints.items():
        if param_name == "self" or param_name == "return" or param_type is None:
            continue
        
        # Handle Optional[Type] -> Type
        origin = get_origin(param_type)
        if origin is not None:
            args = get_args(param_type)
            if args:
                param_type = args[0]
        
        # Get or create provider for this dependency
        if param_type in all_providers:
            dependencies[param_name] = all_providers[param_type]
        elif DIRegistry.is_registered(param_type):
            dep_impl = DIRegistry.get(param_type)
            dep_provider = create_auto_provider(
                param_type, dep_impl, all_providers, visited.copy()
            )
            all_providers[param_type] = dep_provider
            dependencies[param_name] = dep_provider
        else:
            raise ValueError(
                f"Unknown dependency {param_type.__name__} for {implementation_class.__name__}.{param_name}. "
                f"Register it in di_registry.py"
            )
    
    provider = providers.Factory(implementation_class, **dependencies)
    all_providers[interface] = provider
    visited.remove(interface)
    return provider


def create_auto_factory(implementation_class, all_providers):
    """Create a factory provider with auto-resolved dependencies."""
    type_hints = _get_type_hints_safe(implementation_class.__init__)
    dependencies = {}
    
    for param_name, param_type in type_hints.items():
        if param_name == "self" or param_name == "return" or param_type is None:
            continue
        
        origin = get_origin(param_type)
        if origin is not None:
            args = get_args(param_type)
            if args:
                param_type = args[0]
        
        if param_type in all_providers:
            dependencies[param_name] = all_providers[param_type]
        else:
            raise ValueError(
                f"Unknown dependency {param_type.__name__} for {implementation_class.__name__}.{param_name}"
            )
    
    return providers.Factory(implementation_class, **dependencies)


class Container(containers.DeclarativeContainer):
    """Dependency Injection Container."""
    
    config_path = providers.Configuration()
    app_config = providers.Singleton(create_app_config, config_path=config_path)
    db_connection = providers.Singleton(create_db_connection, app_config=app_config)


# Initialize providers
_all_providers: Dict[Type[Any], providers.Provider] = {
    IAppConfig: Container.app_config,
    IDatabaseConnection: Container.db_connection,
}

# Auto-create providers for all registered interfaces
for interface in DIRegistry._registry.keys():
    if interface not in _all_providers:
        implementation = DIRegistry.get(interface)
        provider = create_auto_provider(interface, implementation, _all_providers, set())
        _all_providers[interface] = provider
        # Add as container attribute
        attr_name = interface.__name__[1:].lower() if interface.__name__.startswith("I") else interface.__name__.lower()
        attr_name = attr_name.replace("appconfig", "app_config").replace("databaseconnection", "db_connection")
        setattr(Container, attr_name, provider)

# Create business logic providers
Container.walnut_bl = create_auto_factory(WalnutBL, _all_providers)
