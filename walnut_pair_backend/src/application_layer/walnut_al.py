# src/application_layer/walnut_al.py
from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING
import numpy as np

from src.domain_layer.services.embedding_service import (
    IImageEmbeddingService,
)
from src.common.interfaces import IAppConfig, IDatabaseConnection
from src.infrastructure_layer.db_readers import IWalnutImageEmbeddingReader, IWalnutReader
from src.infrastructure_layer.db_writers import IWalnutWriter
from src.infrastructure_layer.data_access_objects import (
    WalnutDAO,
    WalnutImageDAO,
    WalnutImageEmbeddingDAO,
)


class IWalnutAL(ABC):
    @abstractmethod
    def generate_embeddings(self) -> None:
        pass

    @abstractmethod
    def create_and_save_fake_walnut(self, walnut_id: str) -> WalnutDAO:
        """Create a fake walnut with images and embeddings and save it to the database."""
        pass


class WalnutAL(IWalnutAL):
    def __init__(
        self,
        image_embedding_service: IImageEmbeddingService,
        app_config: IAppConfig,
        db_connection: IDatabaseConnection,
        walnut_image_embedding_reader: IWalnutImageEmbeddingReader,
        walnut_reader: IWalnutReader,
        walnut_writer: IWalnutWriter,
    ) -> None:  
        self.image_embedding_service = image_embedding_service
        self.app_config = app_config
        self.db_connection = db_connection
        self.walnut_image_embedding_reader = walnut_image_embedding_reader
        self.walnut_reader = walnut_reader
        self.walnut_writer = walnut_writer
    
    def generate_embeddings(self) -> None:
        print(self.app_config.image_root)
        image = f"{self.app_config.image_root}/0001/0001_B_1.jpg"
        print(self.app_config.database.host)
        embedding = self.image_embedding_service.generate(image)
        test = self.walnut_image_embedding_reader.get_by_model_name("resnet50-imagenet")
        print(f"Found {len(test)} embeddings")
        walnuts = self.walnut_reader.get_all()
        print(f"Found {len(walnuts)} walnuts")

    def create_and_save_fake_walnut(self, walnut_id: str) -> WalnutDAO:
        """
        Create a fake walnut with images and embeddings and save it to the database.
        This demonstrates the ORM-like save functionality where walnut, images, and embeddings
        are all saved in a single call.
        """
        # Create fake walnut (now it's an ORM model)
        walnut = WalnutDAO(
            id=walnut_id,
            description=f"Fake walnut {walnut_id} for testing",
            created_by="system",
            updated_by="system",
        )

        # Create fake images for all 6 sides
        sides = ["front", "back", "left", "right", "top", "down"]
        for side in sides:
            # Create fake image (now it's an ORM model)
            image = WalnutImageDAO(
                walnut_id=walnut_id,
                side=side,
                image_path=f"/images/{walnut_id}/{walnut_id}_{side[0].upper()}_1.jpg",
                width=1920,
                height=1080,
                checksum=f"fake_checksum_{walnut_id}_{side}",
                created_by="system",
                updated_by="system",
            )

            # Create fake embedding (512-dimensional vector)
            fake_embedding = np.random.rand(512).astype(np.float32)
            embedding = WalnutImageEmbeddingDAO(
                # image_id will be set after image is saved
                model_name="resnet50-imagenet",
                embedding=fake_embedding,
                created_by="system",
                updated_by="system",
            )
            # Attach embedding to image - the writer will set image_id after image is saved
            image.embedding = embedding

            walnut.images.append(image)

        # Save walnut with all images and embeddings using ORM-like save
        saved_walnut = self.walnut_writer.save_with_images(walnut)
        print(f"Successfully saved walnut {walnut_id} with {len(saved_walnut.images)} images")
        return saved_walnut

