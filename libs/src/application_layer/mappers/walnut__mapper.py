# src/application_layer/mappers/walnut__mapper.py
from abc import ABC, abstractmethod
from typing import Dict
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
from src.application_layer.dtos.walnut__dto import WalnutDTO, WalnutImageDTO


class IWalnutMapper(ABC):
    @abstractmethod
    def file_dao_to_entity(self, walnut_file_dao: WalnutFileDAO) -> WalnutEntity:
        pass

    @abstractmethod
    def entity_to_dao(
        self,
        walnut_entity: WalnutEntity,
        walnut_id: str,
        description: str,
        created_by: str,
        updated_by: str,
        model_name: str,
    ) -> WalnutDBDAO:
        pass

    @abstractmethod
    def image_value_object_to_dao(
        self,
        image_vo: ImageValueObject,
        walnut_id: str,
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
    def file_dao_to_entity(self, walnut_file_dao: WalnutFileDAO) -> WalnutEntity:
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
                raise ValueError(
                    f"Invalid side letter '{image_file_dao.side_letter}' in file {image_file_dao.file_path.name}"
                )
            images_by_side[side_enum] = image_file_dao

        required_sides = set(WalnutSideEnum)
        missing_sides = required_sides - set(images_by_side.keys())
        if missing_sides:
            raise ValueError(
                f"Missing required images for sides: {[s.value for s in missing_sides]}"
            )

        image_value_objects: Dict[WalnutSideEnum, ImageValueObject] = {}
        for side_enum, image_file_dao in images_by_side.items():
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

        return WalnutEntity(
            front=image_value_objects[WalnutSideEnum.FRONT],
            back=image_value_objects[WalnutSideEnum.BACK],
            left=image_value_objects[WalnutSideEnum.LEFT],
            right=image_value_objects[WalnutSideEnum.RIGHT],
            top=image_value_objects[WalnutSideEnum.TOP],
            down=image_value_objects[WalnutSideEnum.DOWN],
        )

    def entity_to_dao(
        self,
        walnut_entity: WalnutEntity,
        walnut_id: str,
        description: str = "",
        created_by: str = SYSTEM_USER,
        updated_by: str = SYSTEM_USER,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
    ) -> WalnutDBDAO:
        walnut_dao = WalnutDBDAO(
            id=walnut_id,
            description=description,
            created_by=created_by,
            updated_by=updated_by,
        )

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
            image_dao = self.image_value_object_to_dao(
                image_vo,
                walnut_id,
                created_by=created_by,
                updated_by=updated_by,
            )

            embedding = embedding_mapping[side_enum]
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
        image_vo: ImageValueObject,
        walnut_id: str,
        created_by: str = SYSTEM_USER,
        updated_by: str = SYSTEM_USER,
    ) -> WalnutImageDBDAO:
        return WalnutImageDBDAO(
            walnut_id=walnut_id,
            side=image_vo.side.value,
            image_path=image_vo.path,
            width=image_vo.width,
            height=image_vo.height,
            checksum=image_vo.hash,
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
            images=images,
        )

    def file_dao_to_dto(self, walnut_file_dao: WalnutFileDAO, walnut_id: str) -> WalnutDTO:
        from datetime import datetime
        from src.common.constants import SYSTEM_USER
        
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
            images=images,
        )
