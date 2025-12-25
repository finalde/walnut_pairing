# src/common/di_container.py
"""
Dependency Injection Container - Auto-resolves dependencies from registry.

Usage: Just register interfaces in di_registry.py, everything else is automatic!
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


def create_app_config(config_path: Path) -> IAppConfig:
    return AppConfig.load_from_yaml(config_path)


def create_db_connection(app_config: IAppConfig) -> IDatabaseConnection:
    return psycopg2.connect(
        host=app_config.database.host, port=app_config.database.port,
        database=app_config.database.database, user=app_config.database.user,
        password=app_config.database.password,
    )


def _resolve_type_hints(func):
    """Get type hints with forward references resolved."""
    module = sys.modules.get(func.__module__) if hasattr(func, '__module__') else None
    namespace = {**module.__dict__} if module else {}
    namespace.update({iface.__name__: iface for iface in DIRegistry._registry.keys()})
    namespace.update({'IAppConfig': IAppConfig, 'IDatabaseConnection': IDatabaseConnection})
    try:
        return get_type_hints(func, globalns=namespace)
    except (NameError, TypeError):
        # Fallback: parse annotations manually
        return {name: namespace.get(param.annotation.strip('"\''), param.annotation)
                for name, param in inspect.signature(func).parameters.items()
                if name != "self" and param.annotation != inspect.Parameter.empty
                and (isinstance(param.annotation, str) or not isinstance(param.annotation, str))}


def _create_provider(interface: Type[Any], impl: Type[Any], providers_dict: Dict, visited: set):
    """Create provider with auto-resolved dependencies."""
    if interface in visited:
        raise ValueError(f"Circular dependency: {interface.__name__}")
    if interface in providers_dict:
        return providers_dict[interface]
    
    visited.add(interface)
    hints = _resolve_type_hints(impl.__init__)
    deps = {}
    
    for name, param_type in hints.items():
        if name in ("self", "return") or param_type is None:
            continue
        
        # Unwrap Optional[Type]
        if get_origin(param_type):
            args = get_args(param_type)
            if args:
                param_type = args[0]
        
        # Resolve dependency
        if param_type in providers_dict:
            deps[name] = providers_dict[param_type]
        elif DIRegistry.is_registered(param_type):
            dep_provider = _create_provider(param_type, DIRegistry.get(param_type), providers_dict, visited.copy())
            providers_dict[param_type] = dep_provider
            deps[name] = dep_provider
        else:
            raise ValueError(f"Unknown dependency {param_type.__name__} for {impl.__name__}.{name}")
    
    provider = providers.Factory(impl, **deps)
    providers_dict[interface] = provider
    visited.remove(interface)
    return provider


class Container(containers.DeclarativeContainer):
    """Dependency Injection Container."""
    config_path = providers.Configuration()
    app_config = providers.Singleton(create_app_config, config_path=config_path)
    db_connection = providers.Singleton(create_db_connection, app_config=app_config)


# Auto-create providers for all registered interfaces
_providers = {IAppConfig: Container.app_config, IDatabaseConnection: Container.db_connection}
for interface in DIRegistry._registry.keys():
    if interface not in _providers:
        provider = _create_provider(interface, DIRegistry.get(interface), _providers, set())
        _providers[interface] = provider
        attr = interface.__name__[1:].lower() if interface.__name__.startswith("I") else interface.__name__.lower()
        setattr(Container, attr.replace("appconfig", "app_config").replace("databaseconnection", "db_connection"), provider)

# Create business logic providers
hints = _resolve_type_hints(WalnutBL.__init__)
deps = {}
for name, type_ in hints.items():
    if name not in ("self", "return") and type_:
        if get_origin(type_):
            type_ = get_args(type_)[0] if get_args(type_) else type_
        if type_ in _providers:
            deps[name] = _providers[type_]
Container.walnut_bl = providers.Factory(WalnutBL, **deps)
