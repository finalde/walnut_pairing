# ============================================================
# Imports
# ============================================================

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Type

import psycopg2
from dependency_injector import containers, providers
from sqlalchemy.orm import Session

from application_layer.commands.command_dispatcher import ICommandDispatcher, CommandDispatcher
from application_layer.queries.walnut__query import IWalnutQuery
from common.di_container import (
    DependencyProviderWrapper,
    _container_resolve,
    _create_provider,
    _normalize_attr_name,
)
from common.interfaces import DatabaseConfig, IAppConfig, IDatabaseConnection
from infrastructure_layer.session_factory import SessionFactory

from batch.app_config import AppConfig
from batch.application import Application, IApplication
from batch.di_registry import DIRegistry

if TYPE_CHECKING:
    from batch.di_container import Container


# ============================================================
# Low-level factories (no DI logic)
# ============================================================

def create_app_config(config_path: str | Path) -> IAppConfig:
    """
    Create IAppConfig instance from YAML file.
    
    Args:
        config_path: Path to YAML configuration file (str or Path)
        
    Returns:
        IAppConfig instance
        
    Raises:
        ValueError: If config_path is a dict (wrong usage)
        TypeError: If config_path is not str or Path
    """
    if isinstance(config_path, dict):
        raise ValueError(
            "config_path must be a path, not a dict. "
            "Use container.config_path.from_value(path)"
        )
    if not isinstance(config_path, (str, Path)):
        raise TypeError(f"config_path must be str or Path, got {type(config_path)}")

    path = Path(config_path)
    return AppConfig.load_from_yaml(path)


# Simple factory functions removed - inlined in Container class below


def create_command_dispatcher(container: "Container") -> ICommandDispatcher:
    """
    Factory function to create command dispatcher.
    
    Args:
        container: The Container instance (injected via providers.Self)
        
    Returns:
        ICommandDispatcher instance
    """
    return CommandDispatcher.create_with_handlers(
        dependency_provider=DependencyProviderWrapper(container)
    )


def create_application(
    command_dispatcher: ICommandDispatcher,
    container: "Container",
    app_config: IAppConfig,
) -> IApplication:
    """
    Factory function to create Application instance.
    
    Args:
        command_dispatcher: Command dispatcher instance
        container: Container instance to access walnut_query provider
        app_config: Application configuration
        
    Returns:
        IApplication instance
    """
    return Application(
        command_dispatcher=command_dispatcher,
        walnut_query=container.walnutquery(),
        app_config=app_config,
    )


# ============================================================
# Batch-specific DI Container (composition root)
# ============================================================


class Container(containers.DeclarativeContainer):
    """
    Batch application DI container.
    
    This is the composition root where all batch-specific dependencies are wired together.
    Uses common DI utilities from common.di_container for generic functionality.
    """

    # Configuration
    config_path = providers.Configuration()

    # Core services
    app_config = providers.Singleton(
        create_app_config,
        config_path=config_path,
    )

    database_config = providers.Singleton(
        lambda app_config: app_config.database,
        app_config=app_config,
    )

    db_connection = providers.Singleton(
        lambda database_config: psycopg2.connect(
            host=database_config.host,
            port=database_config.port,
            database=database_config.database,
            user=database_config.user,
            password=database_config.password,
        ),
        database_config=database_config,
    )

    session_factory = providers.Singleton(
        SessionFactory,
        database_config=database_config,
    )

    session = providers.Factory(
        lambda session_factory: session_factory.create_session(),
        session_factory=session_factory,
    )

    # Self reference for container injection
    __self__ = providers.Self()

    command_dispatcher = providers.Factory(
        create_command_dispatcher,
        container=__self__,
    )

    application = providers.Factory(
        create_application,
        command_dispatcher=command_dispatcher,
        container=__self__,
        app_config=app_config,
    )




# ============================================================
# Bootstrap registry → container
# ============================================================

def bootstrap_container() -> Container:
    """
    Build and return a fully-wired DI container.
    This is the single composition root.
    
    This function:
    1. Creates a map of core providers
    2. Registers all DIRegistry interfaces as providers
    3. Sets up provider attributes on Container class
    4. Returns a configured container instance
    
    Returns:
        Fully configured Container instance with all providers registered
    """
    # Start with core providers
    providers_map: Dict[Type[Any], providers.Provider] = {
        IAppConfig: Container.app_config,
        IDatabaseConnection: Container.db_connection,
        SessionFactory: Container.session_factory,
        Session: Container.session,
    }

    # Register all DIRegistry interfaces
    for interface in DIRegistry._registry:
        if interface in providers_map:
            continue

        # Create provider for this interface
        provider = _create_provider(
            interface,
            DIRegistry.get(interface),
            providers_map,
            visited=set(),
        )

        # Add as attribute to Container class
        attr_name = _normalize_attr_name(interface)
        setattr(Container, attr_name, provider)

    return Container()


