# application_layer/commands/command_handlers/walnut__command_handler.py
import numpy as np
from common.constants import DEFAULT_EMBEDDING_MODEL, SYSTEM_USER
from common.enums import WalnutSideEnum
from common.logger import get_logger
from infrastructure_layer.data_access_objects import (
    WalnutDBDAO,
    WalnutImageDBDAO,
    WalnutImageEmbeddingDBDAO,
)
from infrastructure_layer.db_writers import IWalnutDBWriter

from ..command_objects.walnut__command import (
    CreateFakeWalnutCommand,
)
from .base__command_handler import ICommandHandler


class CreateFakeWalnutHandler(ICommandHandler[CreateFakeWalnutCommand]):
    def __init__(
        self,
        walnut_writer: IWalnutDBWriter,
    ) -> None:
        self.walnut_writer: IWalnutDBWriter = walnut_writer
        self.logger = get_logger(__name__)

    def handle(self, command: CreateFakeWalnutCommand) -> None:
        walnut = WalnutDBDAO(
            id=command.walnut_id,
            description=command.description or f"Fake walnut {command.walnut_id} for testing",
            created_by=command.user_id or SYSTEM_USER,
            updated_by=command.user_id or SYSTEM_USER,
        )

        for side_enum in WalnutSideEnum:
            side = side_enum.value
            image = WalnutImageDBDAO(
                walnut_id=command.walnut_id,
                side=side,
                image_path=f"/images/{command.walnut_id}/{command.walnut_id}_{side[0].upper()}_1.jpg",
                width=1920,
                height=1080,
                checksum=f"fake_checksum_{command.walnut_id}_{side}",
                created_by=command.user_id or SYSTEM_USER,
                updated_by=command.user_id or SYSTEM_USER,
            )

            fake_embedding = np.random.rand(2048).astype(np.float32)
            embedding = WalnutImageEmbeddingDBDAO(
                model_name=DEFAULT_EMBEDDING_MODEL,
                embedding=fake_embedding,
                created_by=command.user_id or SYSTEM_USER,
                updated_by=command.user_id or SYSTEM_USER,
            )
            image.embedding = embedding
            walnut.images.append(image)

        saved_walnut = self.walnut_writer.save_with_images(walnut)
        self.logger.info(
            "walnut_saved",
            walnut_id=command.walnut_id,
            image_count=len(saved_walnut.images),
        )
