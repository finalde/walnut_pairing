# src/infrastructure_layer/mappers/entity_to_dao_mapper.py
"""
Mapper to convert domain entities and value objects to DAOs.
"""
from datetime import datetime
from typing import Optional
import numpy as np

from src.domain_layers.entities.walnut_entity import WalnutEntity
from src.domain_layers.value_objects.image_value_object import ImageValueObject
from src.infrastructure_layer.data_access_objects import (
    WalnutDAO,
    WalnutImageDAO,
    WalnutImageEmbeddingDAO,
)
from src.common.enums import WalnutSideEnum


class EntityToDAOMapper:
    """Maps domain entities to data access objects."""

    @staticmethod
    def walnut_entity_to_dao(
        walnut_entity: WalnutEntity,
        walnut_id: str,
        description: str = "",
        created_by: str = "system",
        updated_by: str = "system",
        model_name: str = "resnet50-imagenet",
    ) -> WalnutDAO:
        """
        Convert a WalnutEntity to a WalnutDAO with images and embeddings.

        Args:
            walnut_entity: The domain entity to convert
            walnut_id: The ID for the walnut
            description: Description of the walnut
            created_by: User who created the record
            updated_by: User who last updated the record
            model_name: Model name for embeddings

        Returns:
            WalnutDAO with all images and embeddings populated
        """
        # Create walnut DAO
        walnut_dao = WalnutDAO(
            id=walnut_id,
            description=description,
            created_by=created_by,
            updated_by=updated_by,
        )

        # Map each side to an image DAO
        side_mapping = {
            "front": walnut_entity.front,
            "back": walnut_entity.back,
            "left": walnut_entity.left,
            "right": walnut_entity.right,
            "top": walnut_entity.top,
            "down": walnut_entity.down,
        }

        embedding_mapping = {
            "front": walnut_entity.front_embedding,
            "back": walnut_entity.back_embedding,
            "left": walnut_entity.left_embedding,
            "right": walnut_entity.right_embedding,
            "top": walnut_entity.top_embedding,
            "down": walnut_entity.down_embedding,
        }

        for side_name, image_vo in side_mapping.items():
            image_dao = EntityToDAOMapper.image_value_object_to_dao(
                image_vo,
                walnut_id,
                created_by=created_by,
                updated_by=updated_by,
            )

            # Add embedding if available
            embedding = embedding_mapping[side_name]
            if embedding is not None:
                embedding_dao = WalnutImageEmbeddingDAO(
                    image_id=0,  # Will be set after image is saved
                    model_name=model_name,
                    embedding=embedding,
                    created_by=created_by,
                    updated_by=updated_by,
                )
                image_dao.embedding = embedding_dao

            walnut_dao.images.append(image_dao)

        return walnut_dao

    @staticmethod
    def image_value_object_to_dao(
        image_vo: ImageValueObject,
        walnut_id: str,
        created_by: str = "system",
        updated_by: str = "system",
    ) -> WalnutImageDAO:
        """
        Convert an ImageValueObject to a WalnutImageDAO.

        Args:
            image_vo: The image value object to convert
            walnut_id: The ID of the walnut this image belongs to
            created_by: User who created the record
            updated_by: User who last updated the record

        Returns:
            WalnutImageDAO
        """
        return WalnutImageDAO(
            walnut_id=walnut_id,
            side=image_vo.side.value,  # Convert enum to string
            image_path=image_vo.path,
            width=image_vo.width,
            height=image_vo.height,
            checksum=image_vo.hash,
            created_by=created_by,
            updated_by=updated_by,
        )

