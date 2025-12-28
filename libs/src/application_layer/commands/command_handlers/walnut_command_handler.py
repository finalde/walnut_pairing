# src/application_layer/commands/command_handlers/walnut_command_handler.py
import numpy as np

from .base_handler import ICommandHandler
from ..command_objects.walnut_command import (
    CreateFakeWalnutCommand,
)
from src.common.constants import DEFAULT_EMBEDDING_MODEL, SYSTEM_USER
from src.common.enums import WalnutSideEnum
from src.infrastructure_layer.db_writers import IWalnutDBWriter
from src.infrastructure_layer.data_access_objects import (
    WalnutDBDAO,
    WalnutImageDBDAO,
    WalnutImageEmbeddingDBDAO,
)


class CreateFakeWalnutHandler(ICommandHandler[CreateFakeWalnutCommand]):
    def __init__(
        self,
        walnut_writer: IWalnutDBWriter,
    ) -> None:
        self.walnut_writer: IWalnutDBWriter = walnut_writer

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
        print(f"Successfully saved walnut {command.walnut_id} with {len(saved_walnut.images)} images")
