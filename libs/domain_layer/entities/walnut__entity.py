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
        missing_sides = []
        if not front:
            missing_sides.append("front")
        if not back:
            missing_sides.append("back")
        if not left:
            missing_sides.append("left")
        if not right:
            missing_sides.append("right")
        if not top:
            missing_sides.append("top")
        if not down:
            missing_sides.append("down")

        if missing_sides:
            return Left(MissingSideError(missing_sides))

        for side_name, image_vo in [
            ("front", front),
            ("back", back),
            ("left", left),
            ("right", right),
            ("top", top),
            ("down", down),
        ]:
            if image_vo.width <= 0 or image_vo.height <= 0:
                return Left(InvalidImageError(side_name, f"Invalid dimensions: {image_vo.width}x{image_vo.height}"))
            if image_vo.width > 10000 or image_vo.height > 10000:
                return Left(InvalidImageError(side_name, f"Dimensions too large: {image_vo.width}x{image_vo.height}"))

        image_map = {
            "front": front,
            "back": back,
            "left": left,
            "right": right,
            "top": top,
            "down": down,
        }

        for side_enum in WalnutSideEnum:
            image_vo = image_map[side_enum.value]
            if not image_vo.path:
                return Left(ValidationError(f"Missing path for {side_enum.value} image"))

        valid_formats = {"JPEG", "JPG", "PNG", "BMP", "TIFF"}
        for side_enum in WalnutSideEnum:
            image_vo = image_map[side_enum.value]
            if image_vo.format.upper() not in valid_formats:
                return Left(ValidationError(f"Invalid image format '{image_vo.format}' for {side_enum.value} image"))

        entity = WalnutEntity._create_instance(front, back, left, right, top, down, walnut_id)
        entity.processing_status["validated"] = True
        
        # Calculate dimensions automatically if all images have measurements
        dimension_result = entity._calculate_dimensions()
        if dimension_result.is_right():
            entity.dimensions = dimension_result.value
        
        return Right(entity)

    def _calculate_dimensions(
        self,
        focal_length_px: float = 1000.0,
        min_valid_views: int = 2,
    ) -> Either[WalnutDimensionValueObject, DomainError]:
        """
        Calculate walnut dimensions from image measurements.
        
        Business rules:
        - Maps each view to dimensions based on view orientation
        - Aggregates measurements using median for robustness
        - Requires minimum number of valid views per dimension
        
        Returns:
            Either with WalnutDimensionValueObject or DomainError
        """
        # Collect measurements from all images
        pixel_measurements: Dict[str, list[float]] = {"length": [], "width": [], "height": []}
        camera_distances: list[float] = []
        
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
            
            # Business rule: Map each view to dimensions
            contribution = self._get_view_contribution(side_enum)
            
            for dimension_name, measurement_type in contribution.items():
                if measurement_type == "width":
                    pixel_measurements[dimension_name].append(image_vo.walnut_width_px)
                elif measurement_type == "height":
                    pixel_measurements[dimension_name].append(image_vo.walnut_height_px)
        
        if not camera_distances:
            return Left(ValidationError("No valid measurements found in images"))
        
        # Calculate scale (mm per pixel)
        avg_distance = sum(camera_distances) / len(camera_distances)
        mm_per_px = avg_distance / focal_length_px if focal_length_px > 0 else 0.0
        if mm_per_px <= 0:
            return Left(ValidationError("Invalid camera parameters for dimension calculation"))
        
        # Aggregate dimensions
        dimensions_mm = self._aggregate_dimensions(pixel_measurements, mm_per_px, min_valid_views)
        
        # Create value object with validation
        return WalnutDimensionValueObject.create(
            length_mm=dimensions_mm["length"],
            width_mm=dimensions_mm["width"],
            height_mm=dimensions_mm["height"],
        )

    def _aggregate_dimensions(
        self,
        pixel_measurements: Dict[str, list[float]],
        mm_per_pixel: float,
        min_valid_views: int = 2,
    ) -> Dict[str, float]:
        """
        Aggregate pixel measurements into final dimensions in mm.
        
        Business rule: Use median for robustness against outliers.
        Business rule: Require minimum number of valid views.
        """
        result = {}
        
        for dimension in ["length", "width", "height"]:
            pixel_values = pixel_measurements.get(dimension, [])
            # Filter out zeros (failed measurements)
            valid_pixel_values = [v for v in pixel_values if v > 0]
            
            if len(valid_pixel_values) < min_valid_views:
                result[dimension] = 0.0
            else:
                # Use median for robustness (business rule)
                median_pixels = float(np.median(valid_pixel_values))
                result[dimension] = median_pixels * mm_per_pixel
        
        return result

    @staticmethod
    def _get_view_contribution(side: WalnutSideEnum) -> Dict[str, str]:
        """
        Business rule: What each view contributes to which dimension.
        Returns dict mapping dimension name to which measurement (width/height) to use.
        """
        mapping = {
            WalnutSideEnum.FRONT: {"length": "width", "height": "height"},
            WalnutSideEnum.BACK: {"length": "width", "height": "height"},
            WalnutSideEnum.LEFT: {"width": "width", "height": "height"},
            WalnutSideEnum.RIGHT: {"width": "width", "height": "height"},
            WalnutSideEnum.TOP: {"length": "width", "width": "height"},
            WalnutSideEnum.DOWN: {"length": "width", "width": "height"},
        }
        return mapping.get(side, {})
