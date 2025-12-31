# application_layer/mappers/walnut__mapper.py
from abc import ABC, abstractmethod
from typing import Dict, Optional

import numpy as np
from application_layer.dtos.walnut__dto import WalnutDTO, WalnutImageDTO
from common.constants import DEFAULT_EMBEDDING_MODEL, SYSTEM_USER, UNKNOWN_IMAGE_FORMAT
from common.either import Either, Left
from common.enums import WalnutSideEnum
from common.interfaces import IAppConfig
from common.logger import get_logger
from domain_layer.domain_error import DomainError, MissingSideError, ValidationError
from domain_layer.domain_factories.walnut__domain_factory import WalnutDomainFactory
from domain_layer.entities.walnut__entity import WalnutEntity
from domain_layer.value_objects.walnut_image__value_object import WalnutImageValueObject
from infrastructure_layer.data_access_objects import (
    WalnutDBDAO,
    WalnutImageDBDAO,
    WalnutImageEmbeddingDBDAO,
)
from infrastructure_layer.data_access_objects.walnut__file_dao import WalnutFileDAO, WalnutImageFileDAO
from PIL import Image


class IWalnutMapper(ABC):
    @abstractmethod
    def file_dao_to_entity(self, walnut_file_dao: WalnutFileDAO) -> Either[WalnutEntity, DomainError]:
        pass

    @abstractmethod
    def entity_to_dao(
        self,
        walnut_entity: WalnutEntity,
        description: str,
        created_by: str,
        updated_by: str,
        model_name: str,
    ) -> WalnutDBDAO:
        pass

    @abstractmethod
    def image_value_object_to_dao(
        self,
        image_vo: WalnutImageValueObject,
        walnut_entity: WalnutEntity,
        created_by: str,
        updated_by: str,
    ) -> WalnutImageDBDAO:
        pass

    @abstractmethod
    def dao_to_dto(self, walnut_dao: WalnutDBDAO) -> WalnutDTO:
        pass

    @abstractmethod
    def file_dao_to_dto(self, walnut_file_dao: WalnutFileDAO, walnut_id: str) -> WalnutDTO:
        pass


class WalnutMapper(IWalnutMapper):
    def __init__(self, app_config: IAppConfig) -> None:
        self.app_config: IAppConfig = app_config

    def file_dao_to_entity(self, walnut_file_dao: WalnutFileDAO) -> Either[WalnutEntity, DomainError]:
        side_mapping: Dict[str, WalnutSideEnum] = {
            "F": WalnutSideEnum.FRONT,
            "B": WalnutSideEnum.BACK,
            "L": WalnutSideEnum.LEFT,
            "R": WalnutSideEnum.RIGHT,
            "T": WalnutSideEnum.TOP,
            "D": WalnutSideEnum.DOWN,
        }

        images_by_side: Dict[WalnutSideEnum, WalnutImageFileDAO] = {}
        for image_file_dao in walnut_file_dao.images:
            side_enum = side_mapping.get(image_file_dao.side_letter.upper())
            if side_enum is None:
                return Left[WalnutEntity, DomainError](
                    ValidationError(f"Invalid side letter '{image_file_dao.side_letter}' in file {image_file_dao.file_path.name}")
                )
            images_by_side[side_enum] = image_file_dao

        required_sides = set[WalnutSideEnum](WalnutSideEnum)
        missing_sides = required_sides - set[WalnutSideEnum](images_by_side.keys())
        if missing_sides:
            return Left[WalnutEntity, DomainError][WalnutEntity, DomainError](MissingSideError([s.value for s in missing_sides]))

        from domain_layer.domain_services.embedding__domain_service import ImageEmbeddingDomainService

        image_value_objects: Dict[WalnutSideEnum, WalnutImageValueObject] = {}
        for side_enum, image_file_dao in images_by_side.items():
            try:
                with Image.open(image_file_dao.file_path) as img:
                    img_format = img.format or UNKNOWN_IMAGE_FORMAT
            except Exception as e:
                return Left[WalnutEntity, DomainError](ValidationError(f"Failed to load image {image_file_dao.file_path}: {e}"))

            # Generate embedding for this image
            embedding = ImageEmbeddingDomainService.generate(str(image_file_dao.file_path))

            # Get camera configuration for this side - required, no defaults
            camera_config = self.app_config.get_camera_config(side_enum)
            if camera_config is None:
                return Left[WalnutEntity, DomainError](
                    ValidationError(f"Camera configuration not found for side '{side_enum.value}'. Please configure cameras in config.yml")
                )
            
            camera_distance_mm = camera_config.distance_mm
            focal_length_px = camera_config.focal_length_px

            image_vo = WalnutImageValueObject(
                side=side_enum,
                path=str(image_file_dao.file_path),
                width=image_file_dao.width,
                height=image_file_dao.height,
                format=img_format,
                hash=image_file_dao.checksum,
                embedding=embedding,
                camera_distance_mm=camera_distance_mm,
                focal_length_px=focal_length_px,
                walnut_width_px=0.0,  # Will be set by object finder in command handler
                walnut_height_px=0.0,  # Will be set by object finder in command handler
            )
            image_value_objects[side_enum] = image_vo

        return WalnutDomainFactory.create_from_file_dao_images(image_value_objects, walnut_id=walnut_file_dao.walnut_id)

    def entity_to_dao(
        self,
        walnut_entity: WalnutEntity,
        description: str = "",
        created_by: str = SYSTEM_USER,
        updated_by: str = SYSTEM_USER,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
    ) -> WalnutDBDAO:
        # Extract dimensions from value object (always present - entity is only created with valid dimensions)
        width_mm = walnut_entity.dimensions.width_mm
        height_mm = walnut_entity.dimensions.height_mm
        thickness_mm = walnut_entity.dimensions.thickness_mm

        walnut_dao = WalnutDBDAO(
            id=walnut_entity.id,
            description=description,
            created_by=created_by,
            updated_by=updated_by,
            width_mm=width_mm,
            height_mm=height_mm,
            thickness_mm=thickness_mm,
        )

        side_mapping = {
            WalnutSideEnum.FRONT: walnut_entity.front,
            WalnutSideEnum.BACK: walnut_entity.back,
            WalnutSideEnum.LEFT: walnut_entity.left,
            WalnutSideEnum.RIGHT: walnut_entity.right,
            WalnutSideEnum.TOP: walnut_entity.top,
            WalnutSideEnum.DOWN: walnut_entity.down,
        }

        for side_enum, image_vo in side_mapping.items():
            image_dao = self.image_value_object_to_dao(
                image_vo,
                walnut_entity,
                created_by=created_by,
                updated_by=updated_by,
            )

            # Get embedding from WalnutImageValueObject
            embedding = image_vo.embedding
            if embedding is not None:
                embedding_dao = WalnutImageEmbeddingDBDAO(
                    image_id=0,
                    model_name=model_name,
                    embedding=embedding,
                    created_by=created_by,
                    updated_by=updated_by,
                )
                image_dao.embedding = embedding_dao

            walnut_dao.images.append(image_dao)

        return walnut_dao

    def image_value_object_to_dao(
        self,
        image_vo: WalnutImageValueObject,
        walnut_entity: WalnutEntity,
        created_by: str = SYSTEM_USER,
        updated_by: str = SYSTEM_USER,
    ) -> WalnutImageDBDAO:
        return WalnutImageDBDAO(
            walnut_id=walnut_entity.id,
            side=image_vo.side.value,
            image_path=image_vo.path,
            width=image_vo.width,
            height=image_vo.height,
            checksum=image_vo.hash,
            walnut_width_px=image_vo.walnut_width_px,
            walnut_height_px=image_vo.walnut_height_px,
            camera_distance_mm=image_vo.camera_distance_mm,
            focal_length_px=image_vo.focal_length_px,
            created_by=created_by,
            updated_by=updated_by,
        )

    def dao_to_dto(self, walnut_dao: WalnutDBDAO) -> WalnutDTO:
        images = [
            WalnutImageDTO(
                image_id=img.id,
                walnut_id=img.walnut_id,
                side=img.side,
                image_path=img.image_path,
                width=img.width,
                height=img.height,
                checksum=img.checksum,
                embedding_id=img.embedding.id if img.embedding else None,
            )
            for img in walnut_dao.images
        ]

        return WalnutDTO(
            walnut_id=walnut_dao.id,
            description=walnut_dao.description,
            created_at=walnut_dao.created_at,
            created_by=walnut_dao.created_by,
            updated_at=walnut_dao.updated_at,
            updated_by=walnut_dao.updated_by,
            width_mm=walnut_dao.width_mm,
            height_mm=walnut_dao.height_mm,
            thickness_mm=walnut_dao.thickness_mm,
            images=images,
        )

    def file_dao_to_dto(self, walnut_file_dao: WalnutFileDAO, walnut_id: str) -> WalnutDTO:
        from datetime import datetime

        images = [
            WalnutImageDTO(
                image_id=0,
                walnut_id=walnut_id,
                side=img.side_letter.upper(),
                image_path=str(img.file_path),
                width=img.width,
                height=img.height,
                checksum=img.checksum,
                embedding_id=None,
            )
            for img in walnut_file_dao.images
        ]

        return WalnutDTO(
            walnut_id=walnut_id,
            description=f"Walnut {walnut_id} loaded from filesystem",
            created_at=datetime.now(),
            created_by=SYSTEM_USER,
            updated_at=datetime.now(),
            updated_by=SYSTEM_USER,
            width_mm=None,
            height_mm=None,
            thickness_mm=None,
            images=images,
        )
