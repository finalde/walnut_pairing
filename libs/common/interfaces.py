# common/interfaces.py
"""
Common interfaces for dependency injection.
"""
from abc import ABC, abstractmethod
from typing import Protocol, TYPE_CHECKING, runtime_checkable

if TYPE_CHECKING:
    try:
        from batch.app_config import DatabaseConfig
    except ImportError:
        from typing import Any
        DatabaseConfig = Any


@runtime_checkable
class IDatabaseConnection(Protocol):
    """Protocol for database connection objects."""

    def cursor(self):
        """Create and return a cursor object."""
        ...

    def close(self) -> None:
        """Close the database connection."""
        ...


class IAppConfig(ABC):
    """Interface for application configuration."""

    @property
    @abstractmethod
    def image_root(self) -> str:
        """Get the root path for images."""
        pass

    @property
    @abstractmethod
    def database(self) -> "DatabaseConfig":
        """Get the database configuration."""
        pass

