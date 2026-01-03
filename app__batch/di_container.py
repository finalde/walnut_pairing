# ============================================================
# Batch-specific DI Container and Registry
# ============================================================
# This module contains batch-specific dependency injection setup:
# - Factory functions for batch-specific services
# - Batch Container class with batch-specific providers
# - Batch-specific DIRegistry registrations
# ============================================================
# Note: This file is in app__batch/ directory

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Type

from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession

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
from common.di_registry import DIRegistry, Scope
from common.interfaces import DatabaseConfig, IAppConfig
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

from app__batch.app_config import AppConfig
from app__batch.application import Application


def create_application(
    command_dispatcher: ICommandDispatcher,
    container: "Container",
    app_config: IAppConfig,
) -> Application:
    return Application(
        command_dispatcher=command_dispatcher,
        walnut_query=container.walnut_query(),
        app_config=app_config,
    )


# Register dependencies with scopes
# Singleton: Stateless services that can be shared
DIRegistry.register(IAppConfig, AppConfig, Scope.SINGLETON)
DIRegistry.register(IWalnutMapper, WalnutMapper, Scope.SINGLETON)
DIRegistry.register(IWalnutComparisonMapper, WalnutComparisonMapper, Scope.SINGLETON)
DIRegistry.register(IImageObjectFinder, ImageObjectFinder, Scope.SINGLETON)

# Request/Transient: Services that need per-request instances (using Singleton for batch since it's single-threaded)
DIRegistry.register(IWalnutImageEmbeddingDBReader, WalnutImageEmbeddingDBReader, Scope.SINGLETON)
DIRegistry.register(IWalnutImageDBReader, WalnutImageDBReader, Scope.SINGLETON)
DIRegistry.register(IWalnutImageFileReader, WalnutImageFileReader, Scope.SINGLETON)
DIRegistry.register(IWalnutDBReader, WalnutDBReader, Scope.SINGLETON)
DIRegistry.register(IWalnutImageEmbeddingDBWriter, WalnutImageEmbeddingDBWriter, Scope.SINGLETON)
DIRegistry.register(IWalnutImageDBWriter, WalnutImageDBWriter, Scope.SINGLETON)
DIRegistry.register(IWalnutDBWriter, WalnutDBWriter, Scope.SINGLETON)
DIRegistry.register(IWalnutAL, WalnutAL, Scope.SINGLETON)
DIRegistry.register(IWalnutQuery, WalnutQuery, Scope.SINGLETON)
DIRegistry.register(IWalnutComparisonDBWriter, WalnutComparisonDBWriter, Scope.SINGLETON)


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

    session_factory = providers.Singleton(
        SessionFactory,
        database_config=database_config,
    )

    session = providers.Singleton(
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
    """
    Bootstrap the batch container by creating providers from DIRegistry.
    
    This function:
    1. Creates the container instance first
    2. Creates providers for all registered interfaces with their scopes
    3. Adds them to the container instance
    """
    # Create container instance first
    container = Container()
    
    # Start with core providers that are already in the container
    providers_map: Dict[Type[Any], providers.Provider] = {
        IAppConfig: container.app_config,
        SessionFactory: container.session_factory,
        AsyncSession: container.session,
    }

    # Register all DIRegistry interfaces
    for interface in DIRegistry._registry.keys():
        if interface in providers_map:
            continue

        # Get registration info (implementation and scope)
        registration = DIRegistry.get_registration(interface)
        
        # Create provider for this interface with scope
        provider = _create_provider(
            interface,
            registration.implementation,
            providers_map,
            visited=set(),
            scope=registration.scope,
        )

        # Add as attribute to container instance
        attr_name = _normalize_attr_name(interface)
        setattr(container, attr_name, provider)
        providers_map[interface] = provider

    return container
