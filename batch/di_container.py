# batch/di_container.py
import inspect
import sys
import types
from pathlib import Path
from typing import Any, Dict, Type, get_args, get_origin, get_type_hints

import psycopg2
from application_layer.commands.command_dispatcher import ICommandDispatcher
from common.interfaces import IAppConfig, IDatabaseConnection, IDependencyProvider
from dependency_injector import containers, providers
from infrastructure_layer.session_factory import SessionFactory
from sqlalchemy.orm import Session

from batch.app_config import AppConfig
from batch.application import Application, IApplication
from batch.di_registry import DIRegistry


def create_app_config(config_path: str) -> IAppConfig:
    if isinstance(config_path, dict):
        raise ValueError(
            "config_path must be a string path, not a dict. "
            "Use container.config_path.from_value(str(path)) instead of from_yaml(path)"
        )
    if not isinstance(config_path, (str, Path)):
        raise TypeError(f"config_path must be a string or Path, got {type(config_path)}")
    path = Path(config_path) if isinstance(config_path, str) else config_path
    return AppConfig.load_from_yaml(path)


def create_db_connection(app_config: IAppConfig) -> IDatabaseConnection:
    return psycopg2.connect(
        host=app_config.database.host,
        port=app_config.database.port,
        database=app_config.database.database,
        user=app_config.database.user,
        password=app_config.database.password,
    )


def create_session_factory(app_config: IAppConfig) -> SessionFactory:
    return SessionFactory(app_config)


def create_session(session_factory: SessionFactory) -> Session:
    return session_factory.create_session()


def _resolve_type_hints(func: Any) -> Dict[str, Any]:
    module = sys.modules.get(func.__module__) if hasattr(func, "__module__") else None
    namespace: Dict[str, Any] = {**module.__dict__} if module else {}
    namespace.update({iface.__name__: iface for iface in DIRegistry._registry.keys()})
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
    except (NameError, TypeError):
        return {
            name: namespace.get(param.annotation.strip("\"'"), param.annotation)
            for name, param in inspect.signature(func).parameters.items()
            if name != "self"
            and param.annotation != inspect.Parameter.empty
            and (isinstance(param.annotation, str) or not isinstance(param.annotation, str))
        }


def _create_provider(
    interface: Type[Any], impl: Type[Any], providers_dict: Dict[Type[Any], Any], visited: set[Type[Any]]
) -> Any:
    if interface in visited:
        raise ValueError(f"Circular dependency: {interface.__name__}")
    if interface in providers_dict:
        return providers_dict[interface]

    visited.add(interface)
    hints = _resolve_type_hints(impl.__init__)
    deps = {}

    import inspect

    sig = inspect.signature(impl.__init__)
    for name, param_type in hints.items():
        if name in ("self", "return") or param_type is None:
            continue

        param = sig.parameters.get(name)
        if param and param.default != inspect.Parameter.empty:
            continue

        primitive_types = (int, float, str, bool, bytes, type(None))
        if param_type in primitive_types or isinstance(param_type, type) and issubclass(param_type, primitive_types):
            continue

        if get_origin(param_type):
            args = get_args(param_type)
            if args:
                param_type = args[0]

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


class DependencyProviderWrapper(IDependencyProvider):
    def __init__(self, container: "Container") -> None:
        self._container: Container = container

    def resolve(self, dependency_type: Type[Any]) -> Any:
        return _container_resolve(self._container, dependency_type)


class Container(containers.DeclarativeContainer):
    config_path = providers.Configuration()
    app_config = providers.Singleton(create_app_config, config_path=config_path)
    db_connection = providers.Singleton(create_db_connection, app_config=app_config)
    session_factory = providers.Singleton(create_session_factory, app_config=app_config)
    session = providers.Factory(create_session, session_factory=session_factory)

    def get_provider(self, interface_or_class: Type[Any]) -> Any:
        provider = _providers.get(interface_or_class)
        return provider() if provider else None

    def command_dispatcher(self) -> ICommandDispatcher:
        from application_layer.commands.command_dispatcher import (
            CommandDispatcher,
        )

        return CommandDispatcher.create_with_handlers(
            dependency_provider=DependencyProviderWrapper(self),
        )

    def application(self) -> IApplication:
        cmd_disp = Container.command_dispatcher.__get__(self, Container)()
        return Application(
            command_dispatcher=cmd_disp,
            walnut_query=self.walnutquery(),
            app_config=self.app_config(),
        )


_providers = {
    IAppConfig: Container.app_config,
    IDatabaseConnection: Container.db_connection,
    SessionFactory: Container.session_factory,
    Session: Container.session,
}
for interface in DIRegistry._registry.keys():
    if interface not in _providers:
        provider = _create_provider(interface, DIRegistry.get(interface), _providers, set())
        _providers[interface] = provider
        attr = interface.__name__[1:].lower() if interface.__name__.startswith("I") else interface.__name__.lower()
        attr = (
            attr.replace("appconfig", "app_config")
            .replace("databaseconnection", "db_connection")
            .replace("walnutal", "walnut_al")
        )
        setattr(Container, attr, provider)


def _container_resolve(container: Container, dependency_type: Type[Any]) -> Any:
    attr_name = dependency_type.__name__.lower()
    attr_name = (
        attr_name.replace("iappconfig", "app_config")
        .replace("idatabaseconnection", "db_connection")
        .replace("iwalnutal", "walnut_al")
        .replace("appconfig", "app_config")
        .replace("databaseconnection", "db_connection")
        .replace("walnutal", "walnut_al")
    )
    if hasattr(container, attr_name):
        attr = getattr(container, attr_name)
        if callable(attr):
            return attr()
        return attr

    if DIRegistry.is_registered(dependency_type):
        impl = DIRegistry.get(dependency_type)
        hints = _resolve_type_hints(impl.__init__)
        deps = {}
        for name, param_type in hints.items():
            if name in ("self", "return") or param_type is None:
                continue
            if get_origin(param_type):
                args = get_args(param_type)
                if args:
                    param_type = args[0]
            deps[name] = _container_resolve(container, param_type)
        return impl(**deps)

    hints = _resolve_type_hints(dependency_type.__init__)
    deps = {}
    for name, param_type in hints.items():
        if name in ("self", "return") or param_type is None:
            continue
        if get_origin(param_type):
            args = get_args(param_type)
            if args:
                param_type = args[0]
        deps[name] = _container_resolve(container, param_type)
    return dependency_type(**deps)
