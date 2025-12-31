# infrastructure_layer/services/walnut_image__service.py
from abc import ABC, abstractmethod
from typing import Dict, Tuple

from common.enums import WalnutSideEnum
from domain_layer.domain_services.dimension__domain_service import DimensionDomainService
from domain_layer.value_objects.image__value_object import ImageValueObject

from .image_object__finder import IImageObjectFinder, ObjectDetectionResult


class IWalnutImageService(ABC):
    @abstractmethod
    def estimate_dimensions(
        self,
        images: Dict[WalnutSideEnum, ImageValueObject],
        camera_distance_mm: float = 300.0,
        focal_length_px: float = 1000.0,
        background_is_white: bool = True,
        save_intermediate_results: bool = False,
    ) -> Tuple[float, float, float]:
        """Estimate walnut dimensions (length, width, height) from 6 side images."""
        pass


class WalnutImageService(IWalnutImageService):
    """Simple service for estimating walnut dimensions from 6 orthogonal images."""

    def __init__(self, object_finder: IImageObjectFinder) -> None:
        """Initialize with an image object finder service."""
        self.object_finder: IImageObjectFinder = object_finder

    def estimate_dimensions(
        self,
        images: Dict[WalnutSideEnum, ImageValueObject],
        camera_distance_mm: float = 300.0,
        focal_length_px: float = 1000.0,
        background_is_white: bool = True,
        save_intermediate_results: bool = False,
    ) -> Tuple[float, float, float]:
        """Estimate dimensions using object finder service."""
        # Get camera distances
        camera_distances: Dict[WalnutSideEnum, float] = {}
        for side_enum, image_vo in images.items():
            camera_distances[side_enum] = image_vo.camera_distance_mm or camera_distance_mm

        # Measure dimensions from each view using object finder
        measurements: Dict[str, list[float]] = {"length": [], "width": [], "height": []}

        # FRONT and BACK: give length (width) and height
        for side in [WalnutSideEnum.FRONT, WalnutSideEnum.BACK]:
            result = self.object_finder.find_object(
                images[side].path,
                background_is_white=background_is_white,
            )
            if result and result.width_px > 0 and result.height_px > 0:
                measurements["length"].append(result.width_px)
                measurements["height"].append(result.height_px)

        # LEFT and RIGHT: give width (width) and height
        for side in [WalnutSideEnum.LEFT, WalnutSideEnum.RIGHT]:
            result = self.object_finder.find_object(
                images[side].path,
                background_is_white=background_is_white,
            )
            if result and result.width_px > 0 and result.height_px > 0:
                measurements["width"].append(result.width_px)
                measurements["height"].append(result.height_px)

        # TOP and DOWN: give length (width) and width (height)
        for side in [WalnutSideEnum.TOP, WalnutSideEnum.DOWN]:
            result = self.object_finder.find_object(
                images[side].path,
                background_is_white=background_is_white,
            )
            if result and result.width_px > 0 and result.height_px > 0:
                measurements["length"].append(result.width_px)
                measurements["width"].append(result.height_px)

        # Calculate scale
        avg_distance = sum(camera_distances.values()) / len(camera_distances)
        mm_per_px = avg_distance / focal_length_px if focal_length_px > 0 else 0.0
        if mm_per_px <= 0:
            return (0.0, 0.0, 0.0)

        # Aggregate dimensions
        dimensions_mm = DimensionDomainService.aggregate_dimensions(measurements, mm_per_px)
        return (dimensions_mm["length"], dimensions_mm["width"], dimensions_mm["height"])

