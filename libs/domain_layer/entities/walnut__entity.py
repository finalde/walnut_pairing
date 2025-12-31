# domain_layer/entities/walnut__entity.py
import uuid
from typing import Dict, Optional

import numpy as np
from common.either import Either, Left, Right
from common.enums import WalnutSideEnum
from domain_layer.domain_error import DomainError, InvalidImageError, MissingSideError, ValidationError
from domain_layer.value_objects.image__value_object import ImageValueObject
from domain_layer.value_objects.walnut_dimension__value_object import WalnutDimensionValueObject


class _WalnutEntityBuilder:
    def __init__(
        self,
        front: ImageValueObject,
        back: ImageValueObject,
        left: ImageValueObject,
        right: ImageValueObject,
        top: ImageValueObject,
        down: ImageValueObject,
        walnut_id: Optional[str] = None,
    ) -> None:
        # Use provided ID or generate UUID if not provided
        self._id: str = walnut_id if walnut_id is not None else str(uuid.uuid4())
        self.front: ImageValueObject = front
        self.back: ImageValueObject = back
        self.left: ImageValueObject = left
        self.right: ImageValueObject = right
        self.top: ImageValueObject = top
        self.down: ImageValueObject = down
        self.dimensions: Optional[WalnutDimensionValueObject] = None
        self.processing_status: dict[str, bool] = {"embedding_generated": True, "validated": False}


class WalnutEntity:
    def __new__(
        cls,
        front: ImageValueObject,
        back: ImageValueObject,
        left: ImageValueObject,
        right: ImageValueObject,
        top: ImageValueObject,
        down: ImageValueObject,
    ) -> "WalnutEntity":
        raise RuntimeError("WalnutEntity cannot be instantiated directly. Use WalnutEntity.create() instead.")

    def __init__(
        self,
        front: ImageValueObject,
        back: ImageValueObject,
        left: ImageValueObject,
        right: ImageValueObject,
        top: ImageValueObject,
        down: ImageValueObject,
        walnut_id: Optional[str] = None,
    ) -> None:
        builder = _WalnutEntityBuilder(front, back, left, right, top, down, walnut_id)
        self._id: str = builder._id
        self.front: ImageValueObject = builder.front
        self.back: ImageValueObject = builder.back
        self.left: ImageValueObject = builder.left
        self.right: ImageValueObject = builder.right
        self.top: ImageValueObject = builder.top
        self.down: ImageValueObject = builder.down
        self.dimensions: Optional[WalnutDimensionValueObject] = builder.dimensions
        self.processing_status: dict[str, bool] = builder.processing_status
        self._initialized: bool = True

    def __setattr__(self, name: str, value: object) -> None:
        if hasattr(self, "_initialized") and name == "_id":
            raise AttributeError("Cannot modify _id after initialization")
        super().__setattr__(name, value)

    @property
    def id(self) -> str:
        return self._id

    @classmethod
    def _create_instance(
        cls,
        front: ImageValueObject,
        back: ImageValueObject,
        left: ImageValueObject,
        right: ImageValueObject,
        top: ImageValueObject,
        down: ImageValueObject,
        walnut_id: Optional[str] = None,
    ) -> "WalnutEntity":
        instance = object.__new__(cls)
        instance.__init__(front, back, left, right, top, down, walnut_id)
        return instance

    @staticmethod
    def create(
        front: ImageValueObject,
        back: ImageValueObject,
        left: ImageValueObject,
        right: ImageValueObject,
        top: ImageValueObject,
        down: ImageValueObject,
        walnut_id: Optional[str] = None,
    ) -> Either["WalnutEntity", DomainError]:

        entity = WalnutEntity._create_instance(front, back, left, right, top, down, walnut_id)
        entity.processing_status["validated"] = True
        
        # Calculate dimensions automatically if all images have measurements
        dimension_result = entity._calculate_dimensions()
        if dimension_result.is_right():
            entity.dimensions = dimension_result.value
        
        return Right(entity)

    def _calculate_dimensions(
        self,
        min_valid_views: int = 2,
    ) -> Either[WalnutDimensionValueObject, DomainError]:
        """
        Calculate walnut dimensions from image measurements.
        
        Business rules:
        - Maps each view to walnut dimensions (width/height/thickness) based on view orientation
        - Image measurements (x, y) are just pixel measurements with no domain meaning
        - Aggregates measurements using median for robustness
        - Requires minimum number of valid views per dimension
        - Uses camera parameters (distance and focal length) from each image
        
        Returns:
            Either with WalnutDimensionValueObject or DomainError
        """
        # Collect measurements from all images
        # Mapping to walnut dimensions: width, height, thickness
        pixel_measurements: Dict[str, list[float]] = {"width": [], "height": [], "thickness": []}
        camera_distances: list[float] = []
        focal_lengths: list[float] = []
        
        images = {
            WalnutSideEnum.FRONT: self.front,
            WalnutSideEnum.BACK: self.back,
            WalnutSideEnum.LEFT: self.left,
            WalnutSideEnum.RIGHT: self.right,
            WalnutSideEnum.TOP: self.top,
            WalnutSideEnum.DOWN: self.down,
        }
        
        for side_enum, image_vo in images.items():
            # Check if image has measurements
            if image_vo.walnut_width_px <= 0 or image_vo.walnut_height_px <= 0:
                continue  # Skip images without valid measurements
            
            camera_distances.append(image_vo.camera_distance_mm)
            focal_lengths.append(image_vo.focal_length_px)
            
            # Business rule: Map each view to walnut dimensions
            # Image x, y (pixel measurements) → walnut width, height, thickness
            contribution = self._get_view_contribution(side_enum)
            
            for walnut_dimension, image_measurement_type in contribution.items():
                if image_measurement_type == "width":
                    pixel_measurements[walnut_dimension].append(image_vo.walnut_width_px)
                elif image_measurement_type == "height":
                    pixel_measurements[walnut_dimension].append(image_vo.walnut_height_px)
        
        if not camera_distances:
            return Left(ValidationError("No valid measurements found in images"))
        
        # Calculate scale (mm per pixel) using average camera parameters
        # Business rule: Use average distance and focal length across all cameras
        avg_distance = sum(camera_distances) / len(camera_distances)
        avg_focal_length = sum(focal_lengths) / len(focal_lengths)
        mm_per_px = avg_distance / avg_focal_length if avg_focal_length > 0 else 0.0
        if mm_per_px <= 0:
            return Left(ValidationError("Invalid camera parameters for dimension calculation"))
        
        # Aggregate dimensions
        dimensions_mm = self._aggregate_dimensions(pixel_measurements, mm_per_px, min_valid_views)
        
        # Create value object with validation
        return WalnutDimensionValueObject.create(
            width_mm=dimensions_mm["width"],
            height_mm=dimensions_mm["height"],
            thickness_mm=dimensions_mm["thickness"],
        )

    def _aggregate_dimensions(
        self,
        pixel_measurements: Dict[str, list[float]],
        mm_per_pixel: float,
        min_valid_views: int = 2,
    ) -> Dict[str, float]:
        """
        Aggregate pixel measurements into final walnut dimensions in mm.
        
        Business rule: Use median for robustness against outliers.
        Business rule: Require minimum number of valid views.
        """
        result = {}
        
        for walnut_dimension in ["width", "height", "thickness"]:
            pixel_values = pixel_measurements.get(walnut_dimension, [])
            # Filter out zeros (failed measurements)
            valid_pixel_values = [v for v in pixel_values if v > 0]
            
            if len(valid_pixel_values) < min_valid_views:
                result[walnut_dimension] = 0.0
            else:
                # Use median for robustness (business rule)
                median_pixels = float(np.median(valid_pixel_values))
                result[walnut_dimension] = median_pixels * mm_per_pixel
        
        return result

    @staticmethod
    def _get_view_contribution(side: WalnutSideEnum) -> Dict[str, str]:
        """
        Business rule: What each view contributes to which walnut dimension.
        
        Image measurements (x, y) are just pixel measurements with no domain meaning.
        Walnut dimensions have semantic meaning:
        - width: measured from FRONT/BACK/TOP/DOWN views
        - height: measured from FRONT/BACK/LEFT/RIGHT views
        - thickness: measured from LEFT/RIGHT/TOP/DOWN views
        
        Returns dict mapping walnut dimension (width/height/thickness) to image measurement (width/height).
        """
        mapping = {
            # FRONT/BACK: image x → walnut width, image y → walnut height
            WalnutSideEnum.FRONT: {"width": "width", "height": "height"},
            WalnutSideEnum.BACK: {"width": "width", "height": "height"},
            # LEFT/RIGHT: image x → walnut thickness, image y → walnut height
            WalnutSideEnum.LEFT: {"thickness": "width", "height": "height"},
            WalnutSideEnum.RIGHT: {"thickness": "width", "height": "height"},
            # TOP/DOWN: image x → walnut width, image y → walnut thickness
            WalnutSideEnum.TOP: {"width": "width", "thickness": "height"},
            WalnutSideEnum.DOWN: {"width": "width", "thickness": "height"},
        }
        return mapping.get(side, {})
