from enum import Enum
from typing import List


class WalnutSideEnum(Enum):
    FRONT = "front"
    BACK = "back"
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    DOWN = "down"

    @classmethod
    def list(cls) -> List[str]:
        """Return all sides as a list of strings"""
        return [side.value for side in cls]

class WalnutDimensionTypeEnum(Enum):
    WIDTH = "width"
    HEIGHT = "height"
    THICKNESS = "thickness"

    @classmethod
    def list(cls) -> List[str]:
        """Return all dimensions as a list of strings"""
        return [dimension.value for dimension in cls]


class ImageMeasurementTypeEnum(Enum):
    """Image measurement types - pixel measurements with no domain meaning."""
    WIDTH = "width"
    HEIGHT = "height"

    @classmethod
    def list(cls) -> List[str]:
        """Return all measurement types as a list of strings"""
        return [measurement_type.value for measurement_type in cls]


class ComparisonModeEnum(Enum):
    """Comparison calculation modes."""
    BASIC_ONLY = "basic_only"  # Calculate only basic similarity
    ADVANCED_ONLY = "advanced_only"  # Calculate only advanced similarity
    BOTH = "both"  # Calculate both basic and advanced, then final similarity

    @classmethod
    def list(cls) -> List[str]:
        """Return all comparison modes as a list of strings"""
        return [mode.value for mode in cls]
