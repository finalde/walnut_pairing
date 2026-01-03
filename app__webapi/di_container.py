# app__webapi/di_container.py
"""WebAPI dependency injection container with scope support."""
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Type

from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession

from application_layer.mappers.walnut_comparison__mapper import (
    IWalnutComparisonMapper,
    WalnutComparisonMapper,
)
from application_layer.queries.walnut_comparison__query import (
    IWalnutComparisonQuery,
    WalnutComparisonQuery,
)
from common.di_container import (
    DependencyProviderWrapper,
    _container_resolve,
    _create_provider,
    _normalize_attr_name,
)
from common.di_registry import DIRegistry
from common.interfaces import DatabaseConfig, IAppConfig
from infrastructure_layer.db_readers import (
    IWalnutComparisonDBReader,
    WalnutComparisonDBReader,
)
from infrastructure_layer.session_factory import SessionFactory

from app__webapi.app_config import WebAPIAppConfig

if TYPE_CHECKING:
    pass


# Scope types
class Scope:
    """Dependency injection scope types."""
    SINGLETON = "singleton"  # Single instance for all requests
    REQUEST = "request"  # One instance per request
    TRANSIENT = "transient"  # New instance each time


def create_webapi_app_config(config_path: Path) -> IAppConfig:
    """Create WebAPI app config from YAML file."""
    return WebAPIAppConfig.load_from_yaml(config_path)


class WebAPIContainer(containers.DeclarativeContainer):
    """
    WebAPI application DI container with scope support.
    
    Scopes:
    - Singleton: Single instance shared across all requests
    - Request: One instance per HTTP request (using FastAPI dependency)
    - Transient: New instance created each time
    """

    # Configuration
    config_path = providers.Configuration()

    # Singleton providers (shared across all requests)
    app_config = providers.Singleton(
        create_webapi_app_config,
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

    # Request-scoped providers (one per request)
    # These are created per request using FastAPI's Depends
    session = providers.Factory(
        lambda session_factory: session_factory.create_session(),
        session_factory=session_factory,
    )

    # Singleton mapper (stateless, can be shared)
    walnut_comparison_mapper = providers.Singleton(
        WalnutComparisonMapper,
    )

    # Request-scoped readers and queries
    walnut_comparison_reader = providers.Factory(
        WalnutComparisonDBReader,
        session=session,
    )

    walnut_comparison_query = providers.Factory(
        WalnutComparisonQuery,
        comparison_reader=walnut_comparison_reader,
        comparison_mapper=walnut_comparison_mapper,
    )


def bootstrap_webapi_container(config_path: Path) -> WebAPIContainer:
    """Bootstrap and return the WebAPI container."""
    container = WebAPIContainer()
    container.config_path.from_value(str(config_path))
    return container

