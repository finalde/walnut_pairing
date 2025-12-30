# domain_layer/entities/walnut__entity.py
import uuid
from typing import Optional

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
    ) -> None:
        self._id: str = str(uuid.uuid4())
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
    ) -> None:
        builder = _WalnutEntityBuilder(front, back, left, right, top, down)
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
    ) -> "WalnutEntity":
        instance = object.__new__(cls)
        instance.__init__(front, back, left, right, top, down)
        return instance

    @staticmethod
    def create(
        front: ImageValueObject,
        back: ImageValueObject,
        left: ImageValueObject,
        right: ImageValueObject,
        top: ImageValueObject,
        down: ImageValueObject,
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

        entity = WalnutEntity._create_instance(front, back, left, right, top, down)
        entity.processing_status["validated"] = True
        return Right(entity)

    def set_dimensions(self, dimensions: WalnutDimensionValueObject) -> Either[None, DomainError]:
        """
        Set walnut dimensions using the value object.
        The value object ensures all invariants are satisfied.
        """
        if dimensions is None:
            return Left(ValidationError("Dimensions cannot be None"))
        self.dimensions = dimensions
        return Right(None)
