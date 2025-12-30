# infrastructure_layer/services/walnut_image__service.py
from abc import ABC, abstractmethod
from typing import Dict, Tuple

import numpy as np
from common.enums import WalnutSideEnum
from domain_layer.domain_services.dimension__domain_service import DimensionDomainService
from domain_layer.value_objects.image__value_object import ImageValueObject
from PIL import Image

from .walnut_image_service import (
    IContourFinder,
    IDimensionMeasurer,
    IImageSegmenter,
    ScaleCalculator,
)


class IWalnutImageService(ABC):
    @abstractmethod
    def estimate_dimensions(
        self,
        images: Dict[WalnutSideEnum, ImageValueObject],
        camera_distance_mm: float = 300.0,
        focal_length_px: float = 1000.0,
        background_is_white: bool = True,
        min_contour_size: int = 100,
        save_intermediate_results: bool = False,
    ) -> Tuple[float, float, float]:
        """
        Estimate walnut dimensions (length, width, height) from 6 side images.

        Args:
            images: Dictionary mapping WalnutSideEnum to ImageValueObjects
                Must contain all 6 sides: FRONT, BACK, LEFT, RIGHT, TOP, DOWN
            camera_distance_mm: Distance from camera to walnut in millimeters (default: 300.0)
            focal_length_px: Camera focal length in pixels (default: 1000.0)
            background_is_white: Whether the background is white (default: True)
            min_contour_size: Minimum contour size in pixels (default: 100)
            save_intermediate_results: If True, saves intermediate processing images
                (grayscale, mask, contours, bounding boxes) to _intermediate folder
                under each image's original path. Files are named with pattern:
                {original_name}_intermediate_{step}_{side}.png

        Returns:
            Tuple of (length_mm, width_mm, height_mm) - raw calculation results.
            Returns (0.0, 0.0, 0.0) if calculation fails (e.g., no valid measurements, invalid scale).
            Note: Domain validation should be performed by the application layer.
        """
        pass


class WalnutImageService(IWalnutImageService):
    """Service for estimating walnut dimensions from 6 orthogonal images."""

    def __init__(
        self,
        segmenter: IImageSegmenter,
        contour_finder: IContourFinder,
        measurer: IDimensionMeasurer,
    ) -> None:
        self.segmenter: IImageSegmenter = segmenter
        self.contour_finder: IContourFinder = contour_finder
        self.measurer: IDimensionMeasurer = measurer

    def estimate_dimensions(
        self,
        images: Dict[WalnutSideEnum, ImageValueObject],
        camera_distance_mm: float = 300.0,
        focal_length_px: float = 1000.0,
        background_is_white: bool = True,
        min_contour_size: int = 100,
        save_intermediate_results: bool = False,
    ) -> Tuple[float, float, float]:
        """
        Estimate walnut dimensions using correct view-to-dimension mapping.

        Dimension mapping:
        - length: from FRONT, BACK, TOP, DOWN (width dimension)
        - width: from LEFT, RIGHT, TOP, DOWN (width dimension)
        - height: from FRONT, BACK, LEFT, RIGHT (height dimension)
        """
        # Load images
        image_dict: Dict[WalnutSideEnum, Image.Image] = {}
        camera_distances: Dict[WalnutSideEnum, float] = {}

        for side_enum, image_vo in images.items():
            image_dict[side_enum] = Image.open(image_vo.path).convert("RGB")
            camera_distances[side_enum] = image_vo.camera_distance_mm or camera_distance_mm

        # Measure dimensions from each view
        measurements: Dict[str, list[float]] = {
            "length": [],
            "width": [],
            "height": [],
        }

        # FRONT and BACK: give length (width) and height
        for side in [WalnutSideEnum.FRONT, WalnutSideEnum.BACK]:
            image_array = np.array(image_dict[side])
            width_px, height_px = self.measurer.measure_dimensions(
                image_array,
                images.get(side),
                side,
                save_intermediate_results,
                background_is_white=background_is_white,
                min_contour_size=min_contour_size,
            )
            if width_px > 0 and height_px > 0:
                measurements["length"].append(width_px)  # Width in front/back view = length
                measurements["height"].append(height_px)  # Height in front/back view = height

        # LEFT and RIGHT: give width (width) and height
        for side in [WalnutSideEnum.LEFT, WalnutSideEnum.RIGHT]:
            image_array = np.array(image_dict[side])
            width_px, height_px = self.measurer.measure_dimensions(
                image_array,
                images.get(side),
                side,
                save_intermediate_results,
                background_is_white=background_is_white,
                min_contour_size=min_contour_size,
            )
            if width_px > 0 and height_px > 0:
                measurements["width"].append(width_px)  # Width in left/right view = width
                measurements["height"].append(height_px)  # Height in left/right view = height

        # TOP and DOWN: give length (width) and width (height)
        for side in [WalnutSideEnum.TOP, WalnutSideEnum.DOWN]:
            image_array = np.array(image_dict[side])
            width_px, height_px = self.measurer.measure_dimensions(
                image_array,
                images.get(side),
                side,
                save_intermediate_results,
                background_is_white=background_is_white,
                min_contour_size=min_contour_size,
            )
            if width_px > 0 and height_px > 0:
                measurements["length"].append(width_px)  # Width in top/down view = length
                measurements["width"].append(height_px)  # Height in top/down view = width

        # Calculate scale (use average camera distance)
        avg_distance = sum(camera_distances.values()) / len(camera_distances)
        scale_calculator = ScaleCalculator()
        mm_per_px = scale_calculator.calculate_scale(avg_distance, focal_length_px=focal_length_px)

        if mm_per_px <= 0:
            return (0.0, 0.0, 0.0)

        # Aggregate pixel dimensions using domain service
        dimensions_mm = DimensionDomainService.aggregate_dimensions(measurements, mm_per_px)

        # Return raw calculation results - domain validation should be done in application layer
        return (dimensions_mm["length"], dimensions_mm["width"], dimensions_mm["height"])
