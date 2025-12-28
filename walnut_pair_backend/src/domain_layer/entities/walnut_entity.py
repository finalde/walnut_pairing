# src/domain_layer/entities/walnut_entity.py
from typing import Optional
from src.domain_layer.value_objects.image_value_object import ImageValueObject
from src.common.enums import WalnutSideEnum
import numpy as np


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
        self.front = front
        self.back = back
        self.left = left
        self.right = right
        self.top = top
        self.down = down

        # Mutable states
        self.front_embedding: Optional[np.ndarray] = None
        self.back_embedding: Optional[np.ndarray] = None
        self.left_embedding: Optional[np.ndarray] = None
        self.right_embedding: Optional[np.ndarray] = None
        self.top_embedding: Optional[np.ndarray] = None
        self.down_embedding: Optional[np.ndarray] = None

        self.paired_walnut_id: Optional[str] = None
        self.processing_status: dict[str, bool] = {
            "embedding_generated": False,
            "validated": False
        }

    def set_embedding(self, side: str, embedding: np.ndarray) -> None:
        # Validate side using enum
        valid_sides = {side_enum.value for side_enum in WalnutSideEnum}
        if side not in valid_sides:
            raise ValueError(f"Invalid side: {side}. Must be one of {valid_sides}")
        setattr(self, f"{side}_embedding", embedding)
        # Check if all embeddings are set
        all_set = all(
            getattr(self, f"{side_enum.value}_embedding") is not None
            for side_enum in WalnutSideEnum
        )
        self.processing_status["embedding_generated"] = all_set

    def pair_with(self, walnut_id: str) -> None:
        self.paired_walnut_id = walnut_id
