# src/domain_layers/entities/walnut_entity.py
from typing import Optional
from src.domain_layers.value_objects.image_value_object import ImageValueObject
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
        if side not in ["front", "back", "left", "right", "top", "down"]:
            raise ValueError(f"Invalid side: {side}")
        setattr(self, f"{side}_embedding", embedding)
        # Check if all embeddings are set
        all_set = all(
            getattr(self, f"{s}_embedding") is not None
            for s in ["front", "back", "left", "right", "top", "down"]
        )
        self.processing_status["embedding_generated"] = all_set

    def pair_with(self, walnut_id: str) -> None:
        self.paired_walnut_id = walnut_id
