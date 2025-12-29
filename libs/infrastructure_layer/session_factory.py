# infrastructure_layer/session_factory.py
"""SQLAlchemy session factory and database connection management."""
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Protocol, Callable

from common.interfaces import IAppConfig
from infrastructure_layer.data_access_objects.base__db_dao import Base


class ISessionFactory(Protocol):
    """Protocol for session factory."""
    def create_session(self) -> Session:
        """Create a new database session."""
        ...


class SessionFactory:
    """Factory for creating SQLAlchemy sessions."""
    
    def __init__(self, app_config: IAppConfig) -> None:
        """
        Initialize the session factory with database configuration.

        Args:
            app_config: Application configuration containing database settings
        """
        db_config = app_config.database
        # Create database URL for SQLAlchemy
        database_url = (
            f"postgresql://{db_config.user}:{db_config.password}"
            f"@{db_config.host}:{db_config.port}/{db_config.database}"
        )
        
        # Create engine with pgvector support
        self.engine: Engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL query logging
            pool_pre_ping=True,  # Verify connections before using
        )
        
        # Create session factory
        self.SessionLocal: Callable[[], Session] = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
        )
        
        # Create tables if they don't exist (optional, for development)
        # In production, you'd typically use migrations
        Base.metadata.create_all(bind=self.engine)
    
    def create_session(self) -> Session:
        """Create a new database session."""
        return self.SessionLocal()

