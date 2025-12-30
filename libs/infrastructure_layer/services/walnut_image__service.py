# infrastructure_layer/services/walnut_image__service.py
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple

import numpy as np
from common.enums import WalnutSideEnum
from domain_layer.domain_services.dimension__domain_service import DimensionDomainService
from domain_layer.value_objects.image__value_object import ImageValueObject
from domain_layer.value_objects.walnut_dimension__value_object import WalnutDimensionValueObject
from PIL import Image

from .walnut_image_service import (
    ContourFinder,
    DimensionMeasurer,
    DimensionValidator,
    ImageSegmenter,
    ScaleCalculator,
)


class IWalnutImageService(ABC):
    @abstractmethod
    def estimate_dimensions(
        self,
        images: Dict[WalnutSideEnum, ImageValueObject],
        camera_quality_factor: Optional[float] = None,
        save_intermediate_results: bool = False,
    ) -> Tuple[float, float, float]:
        """
        Estimate walnut dimensions (length, width, height) from 6 side images.

        Args:
            images: Dictionary mapping WalnutSideEnum to ImageValueObjects
                Must contain all 6 sides: FRONT, BACK, LEFT, RIGHT, TOP, DOWN
            camera_quality_factor: Quality factor (0.0-1.0) affecting segmentation sensitivity.
                - 0.0 = Low quality camera (noisy images)
                - 1.0 = High quality camera (clean images)
                - Default: Uses service's default_camera_quality_factor
            save_intermediate_results: If True, saves intermediate processing images
                (grayscale, mask, contours, bounding boxes) to _intermediate folder
                under each image's original path. Files are named with pattern:
                {original_name}_intermediate_{step}_{side}.png

        Returns:
            Tuple of (length_mm, width_mm, height_mm) or (0.0, 0.0, 0.0) if validation fails.
            Dimensions are validated against domain rules (20-50mm range, height <= length).
        """
        pass


class WalnutImageService(IWalnutImageService):
    """Service for estimating walnut dimensions from 6 orthogonal images."""

    def __init__(
        self,
        default_camera_distance_mm: float = 300.0,
        default_camera_quality_factor: float = 0.7,
        default_walnut_size_mm: float = 30.0,
        background_is_white: bool = True,
    ) -> None:
        self.default_camera_distance_mm: float = default_camera_distance_mm
        self.default_camera_quality_factor: float = default_camera_quality_factor
        self.default_walnut_size_mm: float = default_walnut_size_mm

        # Initialize components
        self.segmenter: ImageSegmenter = ImageSegmenter(background_is_white=background_is_white)
        self.contour_finder: ContourFinder = ContourFinder(min_contour_size=100)
        self.validator: DimensionValidator = DimensionValidator()
        self.measurer: DimensionMeasurer = DimensionMeasurer(
            segmenter=self.segmenter,
            contour_finder=self.contour_finder,
            validator=self.validator,
        )
        self.scale_calculator: ScaleCalculator = ScaleCalculator(
            default_camera_distance_mm=default_camera_distance_mm,
        )

    def estimate_dimensions(
        self,
        images: Dict[WalnutSideEnum, ImageValueObject],
        camera_quality_factor: Optional[float] = None,
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
            camera_distances[side_enum] = image_vo.camera_distance_mm or self.default_camera_distance_mm

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
            )
            if width_px > 0 and height_px > 0:
                measurements["length"].append(width_px)  # Width in top/down view = length
                measurements["width"].append(height_px)  # Height in top/down view = width

        # Calculate scale (use average camera distance)
        avg_distance = sum(camera_distances.values()) / len(camera_distances)
        mm_per_px = self.scale_calculator.calculate_scale(avg_distance)

        if mm_per_px <= 0:
            return (0.0, 0.0, 0.0)

        # Aggregate pixel dimensions using domain service
        dimensions_mm = DimensionDomainService.aggregate_dimensions(measurements, mm_per_px)

        if dimensions_mm["length"] == 0 or dimensions_mm["width"] == 0 or dimensions_mm["height"] == 0:
            return (0.0, 0.0, 0.0)

        # Validate using domain value object
        # Note: If caller wants different min/max, they should be validated at application layer
        # Domain layer enforces stable business rules
        dimension_result = WalnutDimensionValueObject.create(
            length_mm=dimensions_mm["length"],
            width_mm=dimensions_mm["width"],
            height_mm=dimensions_mm["height"],
        )

        if dimension_result.is_left():
            return (0.0, 0.0, 0.0)

        dim_vo = dimension_result.value
        return (dim_vo.length_mm, dim_vo.width_mm, dim_vo.height_mm)
