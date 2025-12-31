# common/interfaces.py
"""
Common interfaces for dependency injection.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional, Protocol, runtime_checkable

from common.enums import WalnutSideEnum


@runtime_checkable
class IDatabaseConnection(Protocol):
    """Protocol for database connection objects."""

    def cursor(self):
        """Create and return a cursor object."""
        ...

    def close(self) -> None:
        """Close the database connection."""
        ...
@dataclass
class DatabaseConfig:
    host: str
    port: int
    database: str
    user: str
    password: str


@dataclass
class CameraConfig:
    """Configuration for a single camera."""
    distance_mm: float
    focal_length_px: float

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

    @property
    @abstractmethod
    def cameras(self) -> Dict["WalnutSideEnum", "CameraConfig"]:
        """Get camera configurations by side."""
        pass

    @abstractmethod
    def get_camera_config(self, side: "WalnutSideEnum") -> Optional["CameraConfig"]:
        """Get camera configuration for a specific side."""
        pass


class IDependencyProvider(ABC):
    """Interface for dependency injection provider."""

    @abstractmethod
    def resolve(self, dependency_type: type) -> Any:
        """Resolve a dependency by type."""
        pass
