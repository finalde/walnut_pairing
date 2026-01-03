# ============================================================
# Batch-specific DI Container and Registry
# ============================================================
# This module contains batch-specific dependency injection setup:
# - Factory functions for batch-specific services
# - Batch Container class with batch-specific providers
# - Batch-specific DIRegistry registrations
# ============================================================

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Type

import psycopg2
from dependency_injector import containers, providers
from sqlalchemy.orm import Session

from application_layer.commands.command_dispatcher import ICommandDispatcher, CommandDispatcher
from application_layer.mappers.walnut__mapper import IWalnutMapper, WalnutMapper
from application_layer.mappers.walnut_comparison__mapper import IWalnutComparisonMapper, WalnutComparisonMapper
from application_layer.queries import IWalnutQuery, WalnutQuery
from application_layer.walnut__al import IWalnutAL, WalnutAL
from common.di_container import (
    DependencyProviderWrapper,
    _container_resolve,
    _create_provider,
    _normalize_attr_name,
)
from common.di_registry import DIRegistry
from common.interfaces import DatabaseConfig, IAppConfig, IDatabaseConnection
from infrastructure_layer.db_readers import (
    IWalnutDBReader,
    IWalnutImageDBReader,
    IWalnutImageEmbeddingDBReader,
    WalnutDBReader,
    WalnutImageDBReader,
    WalnutImageEmbeddingDBReader,
)
from infrastructure_layer.db_writers import (
    IWalnutComparisonDBWriter,
    IWalnutDBWriter,
    IWalnutImageDBWriter,
    IWalnutImageEmbeddingDBWriter,
    WalnutComparisonDBWriter,
    WalnutDBWriter,
    WalnutImageDBWriter,
    WalnutImageEmbeddingDBWriter,
)
from infrastructure_layer.file_readers import (
    IWalnutImageFileReader,
    WalnutImageFileReader,
)
from infrastructure_layer.services import (
    IImageObjectFinder,
    ImageObjectFinder,
)
from infrastructure_layer.session_factory import SessionFactory

from batch.app_config import AppConfig
from batch.application import Application


def create_application(
    command_dispatcher: ICommandDispatcher,
    container: "Container",
    app_config: IAppConfig,
) -> Application:
    return Application(
        command_dispatcher=command_dispatcher,
        walnut_query=container.walnutquery(),
        app_config=app_config,
    )


DIRegistry.register(IAppConfig, AppConfig)
DIRegistry.register(IWalnutImageEmbeddingDBReader, WalnutImageEmbeddingDBReader)
DIRegistry.register(IWalnutImageDBReader, WalnutImageDBReader)
DIRegistry.register(IWalnutImageFileReader, WalnutImageFileReader)
DIRegistry.register(IWalnutDBReader, WalnutDBReader)
DIRegistry.register(IWalnutImageEmbeddingDBWriter, WalnutImageEmbeddingDBWriter)
DIRegistry.register(IWalnutImageDBWriter, WalnutImageDBWriter)
DIRegistry.register(IWalnutDBWriter, WalnutDBWriter)
DIRegistry.register(IWalnutAL, WalnutAL)
DIRegistry.register(IWalnutMapper, WalnutMapper)
DIRegistry.register(IWalnutQuery, WalnutQuery)
DIRegistry.register(IImageObjectFinder, ImageObjectFinder)
DIRegistry.register(IWalnutComparisonDBWriter, WalnutComparisonDBWriter)
DIRegistry.register(IWalnutComparisonMapper, WalnutComparisonMapper)


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
        lambda config_path: AppConfig.load_from_yaml(Path(config_path)),
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
        lambda container: CommandDispatcher.create_with_handlers(
            dependency_provider=DependencyProviderWrapper(container)
        ),
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
