# src/common/di_container.py
"""
Dependency Injection Container using dependency-injector framework.
This module configures and provides all application dependencies.
"""
from dependency_injector import containers, providers
from pathlib import Path
import psycopg2

from src.common.app_config import AppConfig
from src.common.interfaces import IAppConfig, IDatabaseConnection
from src.domain_layers.services.embedding_service import (
    IImageEmbeddingService,
    ImageEmbeddingService,
)
from src.business_layers.walnut_bl import IWalnutBL, WalnutBL
from src.data_access_layers.db_readers import (
    IWalnutReader,
    WalnutReader,
    IWalnutImageReader,
    WalnutImageReader,
    IWalnutImageEmbeddingReader,
    WalnutImageEmbeddingReader,
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


class Container(containers.DeclarativeContainer):
    """Dependency Injection Container for the application."""

    # Configuration path - will be set from YAML file
    config_path = providers.Configuration()

    # AppConfig factory - loads from YAML
    app_config = providers.Singleton(
        create_app_config,
        config_path=config_path,
    )

    # Database connection factory
    db_connection = providers.Singleton(
        create_db_connection,
        app_config=app_config,
    )

    # Readers (data access layer)
    walnut_image_embedding_reader = providers.Factory(
        WalnutImageEmbeddingReader,
        db_connection=db_connection,
    )

    walnut_image_reader = providers.Factory(
        WalnutImageReader,
        db_connection=db_connection,
        embedding_reader=walnut_image_embedding_reader,
    )

    walnut_reader = providers.Factory(
        WalnutReader,
        db_connection=db_connection,
        image_reader=walnut_image_reader,
    )

    # Services (domain layer)
    image_embedding_service = providers.Factory(ImageEmbeddingService)

    # Business logic layer
    walnut_bl = providers.Factory(
        WalnutBL,
        image_embedding_service=image_embedding_service,
        app_config=app_config,
        db_connection=db_connection,
    )

