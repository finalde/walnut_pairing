# common/interfaces.py
"""
Common interfaces for dependency injection.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional, Protocol, runtime_checkable

from common.enums import ComparisonModeEnum, WalnutSideEnum


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


@dataclass
class BasicSimilarityConfig:
    """Configuration for basic similarity calculation (dimension-based)."""
    width_weight: float
    height_weight: float
    thickness_weight: float
    skip_advanced_threshold: float  # Skip advanced if basic similarity is below this


@dataclass
class AdvancedSimilarityConfig:
    """Configuration for advanced similarity calculation (embedding-based)."""
    front_weight: float
    back_weight: float
    left_weight: float
    right_weight: float
    top_weight: float
    down_weight: float
    discriminative_power: float  # Power transformation to make high scores rarer
    min_expected_cosine: float  # Minimum expected cosine similarity for normalization
    max_expected_cosine: float  # Maximum expected cosine similarity for normalization


@dataclass
class FinalSimilarityConfig:
    """Configuration for final similarity calculation (combining basic and advanced)."""
    basic_weight: float
    advanced_weight: float


@dataclass
class AlgorithmConfig:
    """Configuration for walnut comparison algorithm."""
    comparison_mode: str  # "basic_only", "advanced_only", or "both"
    basic: BasicSimilarityConfig
    advanced: AdvancedSimilarityConfig
    final: FinalSimilarityConfig

    @property
    def comparison_mode_enum(self) -> ComparisonModeEnum:
        """Get comparison mode."""
        print("sasafsafd")
        return ComparisonModeEnum(self.comparison_mode)


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

    @property
    @abstractmethod
    def algorithm(self) -> Optional["AlgorithmConfig"]:
        """Get algorithm comparison configuration (weights)."""
        pass


class IDependencyProvider(ABC):
    """Interface for dependency injection provider."""

    @abstractmethod
    def resolve(self, dependency_type: type) -> Any:
        """Resolve a dependency by type."""
        pass
