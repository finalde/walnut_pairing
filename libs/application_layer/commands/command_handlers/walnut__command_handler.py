# application_layer/commands/command_handlers/walnut__command_handler.py
from pathlib import Path
from typing import Dict, Optional

from domain_layer.domain_services.dimension__domain_service import ViewMeasurement
from infrastructure_layer.services.image_object__finder import ObjectDetectionResult
import numpy as np
from application_layer.commands.command_handlers.base__command_handler import ICommandHandler
from application_layer.commands.command_objects.walnut__command import CreateFakeWalnutCommand, CreateWalnutFromImagesCommand
from application_layer.dtos.walnut__create_dto import WalnutCreateDTO, WalnutImageCreateDTO
from application_layer.mappers.walnut__mapper import IWalnutMapper
from common.constants import DEFAULT_EMBEDDING_MODEL, SYSTEM_USER
from common.either import Either, Left, Right
from common.enums import WalnutSideEnum
from common.interfaces import IAppConfig
from common.logger import get_logger
from domain_layer.domain_error import DomainError, ValidationError
from domain_layer.domain_factories.walnut__domain_factory import WalnutDomainFactory
from domain_layer.domain_services.embedding__domain_service import ImageEmbeddingDomainService
from domain_layer.entities.walnut__entity import WalnutEntity
from domain_layer.value_objects.image__value_object import ImageValueObject
from domain_layer.value_objects.walnut_dimension__value_object import WalnutDimensionValueObject
from infrastructure_layer.data_access_objects import WalnutFileDAO
from infrastructure_layer.db_writers import IWalnutDBWriter
from infrastructure_layer.file_readers.walnut_image__file_reader import IWalnutImageFileReader
from infrastructure_layer.services import IImageObjectFinder, IWalnutImageService
from common.constants import UNKNOWN_IMAGE_FORMAT
from PIL import Image


class CreateWalnutFromImagesHandler(ICommandHandler[CreateWalnutFromImagesCommand]):
    def __init__(
        self,
        app_config: IAppConfig,
        walnut_writer: IWalnutDBWriter,
        walnut_mapper: IWalnutMapper,
        walnut_image_service: IWalnutImageService,
        walnut_image_file_reader: IWalnutImageFileReader,
        image_object_finder: IImageObjectFinder,
    ) -> None:
        self.app_config: IAppConfig = app_config
        self.walnut_writer: IWalnutDBWriter = walnut_writer
        self.walnut_mapper: IWalnutMapper = walnut_mapper
        self.walnut_image_service: IWalnutImageService = walnut_image_service
        self.walnut_image_file_reader: IWalnutImageFileReader = walnut_image_file_reader
        self.image_object_finder: IImageObjectFinder = image_object_finder
        self.logger = get_logger(__name__)

    def handle(self, command: CreateWalnutFromImagesCommand) -> None:
        image_root = Path(self.app_config.image_root)
        image_directory = image_root / command.walnut_id
        image_intermediate_dir = str(image_root / command.walnut_id / "_intermediate")

        walnut_file_dao: WalnutFileDAO = self.walnut_image_file_reader.load_walnut_from_directory(
            command.walnut_id, image_directory
        )

        # First, create image value objects from file DAO
        side_mapping: Dict[str, WalnutSideEnum] = {
            "F": WalnutSideEnum.FRONT,
            "B": WalnutSideEnum.BACK,
            "L": WalnutSideEnum.LEFT,
            "R": WalnutSideEnum.RIGHT,
            "T": WalnutSideEnum.TOP,
            "D": WalnutSideEnum.DOWN,
        }

        images_by_side: Dict[WalnutSideEnum, ImageValueObject] = {}
        for image_file_dao in walnut_file_dao.images:
            side_enum = side_mapping.get(image_file_dao.side_letter.upper())
            if side_enum is None:
                self.logger.error("invalid_side_letter", side_letter=image_file_dao.side_letter, walnut_id=command.walnut_id)
                return
            
            with Image.open(image_file_dao.file_path) as img:
                img_format = img.format or UNKNOWN_IMAGE_FORMAT

            # Generate embedding for this image
            embedding = ImageEmbeddingDomainService.generate(str(image_file_dao.file_path))
            result: Optional[ObjectDetectionResult] = self.image_object_finder.find_object(
                image_vo.path,
                background_is_white=True,
                intermediate_dir=image_intermediate_dir,
            )
            if result is None:
                self.logger.error("object_detection_failed", walnut_id=command.walnut_id, side=side_enum.value)
                return

            image_vo = ImageValueObject(
                side=side_enum,
                path=str(image_file_dao.file_path),
                width=image_file_dao.width,
                height=image_file_dao.height,
                format=img_format,
                hash=image_file_dao.checksum,
                embedding=embedding,
                camera_distance_mm=300,
                walnut_width_px=result.width_px,
                walnut_height_px=result.height_px,
            )
            images_by_side[side_enum] = image_vo


        entity_result: Either[WalnutEntity, DomainError] = WalnutDomainFactory.create_from_file_dao_images(images_by_side, walnut_id=command.walnut_id)
        if entity_result.is_left():
            error = entity_result.value
            self.logger.error("entity_creation_failed", walnut_id=command.walnut_id, error=str(error))
            return

        walnut_entity: WalnutEntity = entity_result.value

        try:
            image_root = Path(self.app_config.image_root)
            intermediate_dir = str(image_root / command.walnut_id / "_intermediate")
            
            measurements = self.walnut_image_service.get_measurements_from_images(
                images=images_by_side,
                background_is_white=True,
                intermediate_dir=intermediate_dir,
            )
            
            # Calculate dimensions using domain service
            from domain_layer.domain_services.dimension__domain_service import DimensionDomainService
            length_mm, width_mm, height_mm = DimensionDomainService.calculate_dimensions_from_measurements(
                measurements=measurements,
                focal_length_px=1000.0,  # TODO: Make this configurable
            )
            
            # Create value object from estimated dimensions - domain validation
            dimension_result = WalnutDimensionValueObject.create(length_mm=length_mm, width_mm=width_mm, height_mm=height_mm)
            if dimension_result.is_left():
                # Domain validation failed - log warning, intermediate results already saved, don't persist to DB
                self.logger.warning(
                    "dimension_validation_failed",
                    walnut_id=walnut_entity.id,
                    error=str(dimension_result.value),
                    length_mm=length_mm,
                    width_mm=width_mm,
                    height_mm=height_mm,
                    note="Intermediate results saved, but walnut not persisted due to invalid dimensions",
                )
                return

            # Validation passed, set dimensions on entity
            set_result = walnut_entity.set_dimensions(dimension_result.value)
            if set_result.is_left():
                # Domain error setting dimensions - log error and stop
                self.logger.error(
                    "dimension_set_failed",
                    walnut_id=walnut_entity.id,
                    error=str(set_result.value),
                )
                return

            self.logger.info(
                "dimensions_estimated",
                walnut_id=walnut_entity.id,
                length_mm=length_mm,
                width_mm=width_mm,
                height_mm=height_mm,
            )
        except Exception as e:
            self.logger.error("dimension_estimation_failed", walnut_id=walnut_entity.id, error=str(e), exc_info=True)
            return

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
