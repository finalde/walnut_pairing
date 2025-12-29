# application_layer/commands/command_handlers/walnut__command_handler.py
import numpy as np
from common.constants import DEFAULT_EMBEDDING_MODEL, SYSTEM_USER
from common.enums import WalnutSideEnum
from common.either import Left, Right
from common.logger import get_logger
from infrastructure_layer.db_writers import IWalnutDBWriter

from application_layer.dtos.walnut__create_dto import WalnutCreateDTO, WalnutImageCreateDTO
from application_layer.mappers.walnut__mapper import IWalnutMapper
from domain_layer.domain_error import ValidationError
from domain_layer.domain_factories.walnut__domain_factory import WalnutDomainFactory
from domain_layer.value_objects.image__value_object import ImageValueObject

from ..command_objects.walnut__command import CreateFakeWalnutCommand
from .base__command_handler import ICommandHandler


class CreateFakeWalnutHandler(ICommandHandler[CreateFakeWalnutCommand]):
    def __init__(
        self,
        walnut_writer: IWalnutDBWriter,
        walnut_mapper: IWalnutMapper,
    ) -> None:
        self.walnut_writer: IWalnutDBWriter = walnut_writer
        self.walnut_mapper: IWalnutMapper = walnut_mapper
        self.logger = get_logger(__name__)

    def handle(self, command: CreateFakeWalnutCommand) -> None:
        create_dto = WalnutCreateDTO(
            description=command.description or f"Fake walnut for testing",
            images=[
                WalnutImageCreateDTO(
                    side=side_enum.value,
                    image_path=f"/images/{command.walnut_id}/{command.walnut_id}_{side_enum.value[0].upper()}_1.jpg",
                    width=1920,
                    height=1080,
                    checksum=f"fake_checksum_{command.walnut_id}_{side_enum.value}",
                )
                for side_enum in WalnutSideEnum
            ],
        )

        side_enum_map = {
            "front": WalnutSideEnum.FRONT,
            "back": WalnutSideEnum.BACK,
            "left": WalnutSideEnum.LEFT,
            "right": WalnutSideEnum.RIGHT,
            "top": WalnutSideEnum.TOP,
            "down": WalnutSideEnum.DOWN,
        }

        images_dict: dict[str, ImageValueObject] = {}
        for img_dto in create_dto.images:
            side_lower = img_dto.side.lower()
            if side_lower not in side_enum_map:
                self.logger.error("invalid_side", side=img_dto.side)
                return

            side_enum = side_enum_map[side_lower]
            image_vo = ImageValueObject(
                side=side_enum,
                path=img_dto.image_path,
                width=img_dto.width,
                height=img_dto.height,
                format="JPEG",
                hash=img_dto.checksum,
            )
            images_dict[side_lower] = image_vo

        entity_result = WalnutDomainFactory.create_from_images(images_dict)
        if entity_result.is_left():
            error = entity_result.value
            self.logger.error("domain_validation_failed", error=str(error))
            return

        walnut_entity = entity_result.value

        for side_enum in WalnutSideEnum:
            fake_embedding = np.random.rand(2048).astype(np.float32)
            embedding_result = walnut_entity.set_embedding(side_enum.value, fake_embedding)
            if embedding_result.is_left():
                error = embedding_result.value
                self.logger.error("embedding_set_failed", walnut_id=walnut_entity.id, side=side_enum.value, error=str(error))
                return

        walnut_dao = self.walnut_mapper.entity_to_dao(
            walnut_entity,
            description=create_dto.description or f"Fake walnut for testing",
            created_by=command.user_id or SYSTEM_USER,
            updated_by=command.user_id or SYSTEM_USER,
            model_name=DEFAULT_EMBEDDING_MODEL,
        )

        saved_walnut = self.walnut_writer.save_with_images(walnut_dao)
        self.logger.info("walnut_saved", walnut_id=walnut_entity.id, image_count=len(saved_walnut.images))
