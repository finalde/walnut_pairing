# src/application_layer/mappers/walnut__mapper.py
"""
Mapper for walnut domain objects.
Handles all mapping logic between walnut domain entities/value objects and other types (DAOs, DTOs, etc.).
"""
from typing import Optional, Dict
import numpy as np
from PIL import Image

from src.infrastructure_layer.data_access_objects.walnut__file_dao import WalnutFileDAO, WalnutImageFileDAO
from src.domain_layer.entities.walnut__entity import WalnutEntity
from src.domain_layer.value_objects.image__value_object import ImageValueObject
from src.infrastructure_layer.data_access_objects import (
    WalnutDBDAO,
    WalnutImageDBDAO,
    WalnutImageEmbeddingDBDAO,
)
from src.common.enums import WalnutSideEnum
from src.common.constants import DEFAULT_EMBEDDING_MODEL, SYSTEM_USER, UNKNOWN_IMAGE_FORMAT


class WalnutMapper:
    """Maps walnut domain objects to and from other representations."""

    @staticmethod
    def file_dao_to_entity(walnut_file_dao: WalnutFileDAO) -> WalnutEntity:
        """
        Convert a WalnutFileDAO to a WalnutEntity with domain validation.

        Args:
            walnut_file_dao: The file DAO loaded from filesystem

        Returns:
            WalnutEntity with all images as value objects

        Raises:
            ValueError: If required images are missing or invalid
        """
        # Map side letters to enum values
        side_mapping: Dict[str, WalnutSideEnum] = {
            "F": WalnutSideEnum.FRONT,
            "B": WalnutSideEnum.BACK,
            "L": WalnutSideEnum.LEFT,
            "R": WalnutSideEnum.RIGHT,
            "T": WalnutSideEnum.TOP,
            "D": WalnutSideEnum.DOWN,
        }

        # Group images by side
        images_by_side: Dict[WalnutSideEnum, WalnutImageFileDAO] = {}
        for image_file_dao in walnut_file_dao.images:
            side_enum = side_mapping.get(image_file_dao.side_letter.upper())
            if side_enum is None:
                raise ValueError(
                    f"Invalid side letter '{image_file_dao.side_letter}' in file {image_file_dao.file_path.name}"
                )
            images_by_side[side_enum] = image_file_dao

        # Validate all required sides are present
        required_sides = set(WalnutSideEnum)
        missing_sides = required_sides - set(images_by_side.keys())
        if missing_sides:
            raise ValueError(
                f"Missing required images for sides: {[s.value for s in missing_sides]}"
            )

        # Convert each image file DAO to ImageValueObject
        image_value_objects: Dict[WalnutSideEnum, ImageValueObject] = {}
        for side_enum, image_file_dao in images_by_side.items():
            # Load image to get format
            try:
                with Image.open(image_file_dao.file_path) as img:
                    img_format = img.format or UNKNOWN_IMAGE_FORMAT
            except Exception as e:
                raise ValueError(
                    f"Failed to load image {image_file_dao.file_path}: {e}"
                ) from e

            image_vo = ImageValueObject(
                side=side_enum,
                path=str(image_file_dao.file_path),
                width=image_file_dao.width,
                height=image_file_dao.height,
                format=img_format,
                hash=image_file_dao.checksum,
            )
            image_value_objects[side_enum] = image_vo

        # Create WalnutEntity with all images
        return WalnutEntity(
            front=image_value_objects[WalnutSideEnum.FRONT],
            back=image_value_objects[WalnutSideEnum.BACK],
            left=image_value_objects[WalnutSideEnum.LEFT],
            right=image_value_objects[WalnutSideEnum.RIGHT],
            top=image_value_objects[WalnutSideEnum.TOP],
            down=image_value_objects[WalnutSideEnum.DOWN],
        )

    @staticmethod
    def entity_to_dao(
        walnut_entity: WalnutEntity,
        walnut_id: str,
        description: str = "",
        created_by: str = SYSTEM_USER,
        updated_by: str = SYSTEM_USER,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
    ) -> WalnutDBDAO:
        """
        Convert a WalnutEntity to a WalnutDBDAO with images and embeddings.

        Args:
            walnut_entity: The domain entity to convert
            walnut_id: The ID for the walnut
            description: Description of the walnut
            created_by: User who created the record
            updated_by: User who last updated the record
            model_name: Model name for embeddings

        Returns:
            WalnutDBDAO with all images and embeddings populated
        """
        # Create walnut DB DAO
        walnut_dao = WalnutDBDAO(
            id=walnut_id,
            description=description,
            created_by=created_by,
            updated_by=updated_by,
        )

        # Map each side to an image DAO using enum
        side_mapping = {
            WalnutSideEnum.FRONT: walnut_entity.front,
            WalnutSideEnum.BACK: walnut_entity.back,
            WalnutSideEnum.LEFT: walnut_entity.left,
            WalnutSideEnum.RIGHT: walnut_entity.right,
            WalnutSideEnum.TOP: walnut_entity.top,
            WalnutSideEnum.DOWN: walnut_entity.down,
        }

        embedding_mapping = {
            WalnutSideEnum.FRONT: walnut_entity.front_embedding,
            WalnutSideEnum.BACK: walnut_entity.back_embedding,
            WalnutSideEnum.LEFT: walnut_entity.left_embedding,
            WalnutSideEnum.RIGHT: walnut_entity.right_embedding,
            WalnutSideEnum.TOP: walnut_entity.top_embedding,
            WalnutSideEnum.DOWN: walnut_entity.down_embedding,
        }

        for side_enum, image_vo in side_mapping.items():
            side_name = side_enum.value
            image_dao = WalnutMapper.image_value_object_to_dao(
                image_vo,
                walnut_id,
                created_by=created_by,
                updated_by=updated_by,
            )

            # Add embedding if available
            embedding = embedding_mapping[side_enum]
            if embedding is not None:
                embedding_dao = WalnutImageEmbeddingDBDAO(
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
        created_by: str = SYSTEM_USER,
        updated_by: str = SYSTEM_USER,
    ) -> WalnutImageDBDAO:
        """
        Convert an ImageValueObject to a WalnutImageDBDAO.

        Args:
            image_vo: The image value object to convert
            walnut_id: The ID of the walnut this image belongs to
            created_by: User who created the record
            updated_by: User who last updated the record

        Returns:
            WalnutImageDBDAO
        """
        return WalnutImageDBDAO(
            walnut_id=walnut_id,
            side=image_vo.side.value,  # Convert enum to string
            image_path=image_vo.path,
            width=image_vo.width,
            height=image_vo.height,
            checksum=image_vo.hash,
            created_by=created_by,
            updated_by=updated_by,
        )

    # Future mapping methods can be added here:
    # - dao_to_entity()
    # - dao_to_value_object()
    # - entity_to_dto()
    # - etc.

