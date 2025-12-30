# application_layer/commands/command_handlers/walnut__command_handler.py
from pathlib import Path
from typing import Dict

import numpy as np
from common.constants import DEFAULT_EMBEDDING_MODEL, SYSTEM_USER
from common.enums import WalnutSideEnum
from common.either import Left, Right
from common.interfaces import IAppConfig
from common.logger import get_logger
from domain_layer.domain_services.embedding__domain_service import ImageEmbeddingDomainService
from infrastructure_layer.db_writers import IWalnutDBWriter
from infrastructure_layer.services import IWalnutImageService

from application_layer.mappers.walnut__mapper import IWalnutMapper
from application_layer.services.walnut_image_loader import WalnutImageLoader
from domain_layer.domain_error import ValidationError
from domain_layer.domain_factories.walnut__domain_factory import WalnutDomainFactory
from domain_layer.value_objects.image__value_object import ImageValueObject

from application_layer.commands.command_objects.walnut__command import CreateFakeWalnutCommand, CreateWalnutFromImagesCommand
from application_layer.commands.command_handlers.base__command_handler import ICommandHandler
from application_layer.dtos.walnut__create_dto import WalnutCreateDTO, WalnutImageCreateDTO
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
                camera_distance_mm=150,
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


class CreateWalnutFromImagesHandler(ICommandHandler[CreateWalnutFromImagesCommand]):
    def __init__(
        self,
        app_config: IAppConfig,
        walnut_writer: IWalnutDBWriter,
        walnut_mapper: IWalnutMapper,
        walnut_image_service: IWalnutImageService,
    ) -> None:
        self.app_config: IAppConfig = app_config
        self.walnut_writer: IWalnutDBWriter = walnut_writer
        self.walnut_mapper: IWalnutMapper = walnut_mapper
        self.walnut_image_service: IWalnutImageService = walnut_image_service
        self.logger = get_logger(__name__)

    def handle(self, command: CreateWalnutFromImagesCommand) -> None:
        image_root = Path(self.app_config.image_root)
        image_directory = image_root / command.walnut_id

        if not image_directory.exists():
            self.logger.error("image_directory_not_found", walnut_id=command.walnut_id, directory=str(image_directory))
            return

        walnut_file_dao = WalnutImageLoader.load_walnut_from_directory(command.walnut_id, image_directory)
        if walnut_file_dao is None:
            self.logger.error("no_images_found", walnut_id=command.walnut_id, directory=str(image_directory))
            return

        self.logger.info(
            "images_loaded",
            walnut_id=command.walnut_id,
            image_count=len(walnut_file_dao.images),
            directory=str(image_directory),
        )

        entity_result = self.walnut_mapper.file_dao_to_entity(walnut_file_dao)
        if entity_result.is_left():
            error = entity_result.value
            self.logger.error("entity_creation_failed", walnut_id=command.walnut_id, error=str(error))
            return

        walnut_entity = entity_result.value
        self.logger.debug("entity_created", walnut_id=walnut_entity.id)

        images_dict: Dict[WalnutSideEnum, ImageValueObject] = {
            WalnutSideEnum.FRONT: walnut_entity.front,
            WalnutSideEnum.BACK: walnut_entity.back,
            WalnutSideEnum.LEFT: walnut_entity.left,
            WalnutSideEnum.RIGHT: walnut_entity.right,
            WalnutSideEnum.TOP: walnut_entity.top,
            WalnutSideEnum.DOWN: walnut_entity.down,
        }

        try:
            length_mm, width_mm, height_mm = self.walnut_image_service.estimate_dimensions(
                images=images_dict,
                save_intermediate_results=command.save_intermediate_results,
            )
            walnut_entity.length_mm = length_mm
            walnut_entity.width_mm = width_mm
            walnut_entity.height_mm = height_mm
            self.logger.info(
                "dimensions_estimated",
                walnut_id=walnut_entity.id,
                length_mm=length_mm,
                width_mm=width_mm,
                height_mm=height_mm,
            )
        except Exception as e:
            self.logger.error("dimension_estimation_failed", walnut_id=walnut_entity.id, error=str(e), exc_info=True)

        for side_enum in WalnutSideEnum:
            image_vo = images_dict[side_enum]
            embedding = ImageEmbeddingDomainService.generate(image_vo.path)
            embedding_result = walnut_entity.set_embedding(side_enum.value, embedding)
            if embedding_result.is_left():
                error = embedding_result.value
                self.logger.error("embedding_set_failed", walnut_id=walnut_entity.id, side=side_enum.value, error=str(error))
                return
            self.logger.debug("embedding_generated", walnut_id=walnut_entity.id, side=side_enum.value)

        walnut_dao = self.walnut_mapper.entity_to_dao(
            walnut_entity,
            description=command.description or f"Walnut {command.walnut_id} loaded from filesystem",
            created_by=command.user_id or SYSTEM_USER,
            updated_by=command.user_id or SYSTEM_USER,
            model_name=DEFAULT_EMBEDDING_MODEL,
        )
        self.logger.debug("entity_to_dao_converted", walnut_id=command.walnut_id)

        saved_walnut = self.walnut_writer.save_with_images(walnut_dao)
        self.logger.info(
            "walnut_saved",
            walnut_id=walnut_entity.id,
            image_count=len(saved_walnut.images),
            length_mm=saved_walnut.length_mm,
            width_mm=saved_walnut.width_mm,
            height_mm=saved_walnut.height_mm,
        )
