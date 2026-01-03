# infrastructure_layer/session_factory.py
"""SQLAlchemy session factory and database connection management."""
from typing import Callable, Protocol

from common.interfaces import DatabaseConfig, IAppConfig
from infrastructure_layer.data_access_objects.base__db_dao import Base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


class ISessionFactory(Protocol):
    """Protocol for session factory."""

    def create_session(self) -> AsyncSession:
        """Create a new database session."""
        ...


class SessionFactory:
    """Factory for creating SQLAlchemy async sessions."""

    def __init__(self, database_config: DatabaseConfig) -> None:
        """
        Initialize the session factory with database configuration.

        Args:
            database_config: Database configuration containing database settings
        """
        # Create database URL for SQLAlchemy async (using asyncpg driver)
        database_url = (
            f"postgresql+asyncpg://{database_config.user}:{database_config.password}"
            f"@{database_config.host}:{database_config.port}/{database_config.database}"
        )

        # Create async engine with pgvector support
        self.engine = create_async_engine(
            database_url,
            echo=False,  # Set to True for SQL query logging
            pool_pre_ping=True,  # Verify connections before using
            poolclass=NullPool,  # Use NullPool for async
        )

        # Create async session factory
        self.SessionLocal: Callable[[], AsyncSession] = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    def create_session(self) -> AsyncSession:
        """Create a new async database session."""
        return self.SessionLocal()
