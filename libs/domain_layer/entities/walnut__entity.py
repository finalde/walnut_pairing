# domain_layer/entities/walnut__entity.py
from typing import Optional

import numpy as np
from common.enums import WalnutSideEnum
from domain_layer.value_objects.image__value_object import ImageValueObject


class WalnutEntity:
    def __init__(
        self,
        front: ImageValueObject,
        back: ImageValueObject,
        left: ImageValueObject,
        right: ImageValueObject,
        top: ImageValueObject,
        down: ImageValueObject,
    ):
        # Validate all images are provided
        if not all([front, back, left, right, top, down]):
            raise ValueError("All six sides must have images")

        # Validate image dimensions are reasonable
        for side_name, image_vo in [
            ("front", front),
            ("back", back),
            ("left", left),
            ("right", right),
            ("top", top),
            ("down", down),
        ]:
            if image_vo.width <= 0 or image_vo.height <= 0:
                raise ValueError(f"Invalid dimensions for {side_name} image: {image_vo.width}x{image_vo.height}")
            if image_vo.width > 10000 or image_vo.height > 10000:
                raise ValueError(f"Image dimensions too large for {side_name}: {image_vo.width}x{image_vo.height}")

        self.front: ImageValueObject = front
        self.back: ImageValueObject = back
        self.left: ImageValueObject = left
        self.right: ImageValueObject = right
        self.top: ImageValueObject = top
        self.down: ImageValueObject = down

        # Mutable states
        self.front_embedding: Optional[np.ndarray] = None
        self.back_embedding: Optional[np.ndarray] = None
        self.left_embedding: Optional[np.ndarray] = None
        self.right_embedding: Optional[np.ndarray] = None
        self.top_embedding: Optional[np.ndarray] = None
        self.down_embedding: Optional[np.ndarray] = None

        self.paired_walnut_id: Optional[str] = None
        self.processing_status: dict[str, bool] = {"embedding_generated": False, "validated": False}

    def validate(self) -> bool:
        """
        Validate the walnut entity.

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        # Check all images have valid paths
        for side_enum in WalnutSideEnum:
            image_vo = getattr(self, side_enum.value)
            if not image_vo.path:
                raise ValueError(f"Missing path for {side_enum.value} image")
            # Path validation could check if file exists, but that's infrastructure concern

        # Check all images have valid formats
        valid_formats = {"JPEG", "JPG", "PNG", "BMP", "TIFF"}
        for side_enum in WalnutSideEnum:
            image_vo = getattr(self, side_enum.value)
            if image_vo.format.upper() not in valid_formats:
                raise ValueError(f"Invalid image format '{image_vo.format}' for {side_enum.value} image")

        self.processing_status["validated"] = True
        return True

    def set_embedding(self, side: str, embedding: np.ndarray) -> None:
        # Validate side using enum
        valid_sides = {side_enum.value for side_enum in WalnutSideEnum}
        if side not in valid_sides:
            raise ValueError(f"Invalid side: {side}. Must be one of {valid_sides}")
        setattr(self, f"{side}_embedding", embedding)
        # Check if all embeddings are set
        all_set = all(getattr(self, f"{side_enum.value}_embedding") is not None for side_enum in WalnutSideEnum)
        self.processing_status["embedding_generated"] = all_set

    def pair_with(self, walnut_id: str) -> None:
        self.paired_walnut_id: Optional[str] = walnut_id
