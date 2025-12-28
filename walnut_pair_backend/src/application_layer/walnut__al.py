# src/application_layer/walnut__al.py
from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING
import numpy as np

from pathlib import Path
from src.domain_layer.services.embedding__service import (
    IImageEmbeddingService,
)
from src.common.interfaces import IAppConfig, IDatabaseConnection
from src.common.constants import DEFAULT_EMBEDDING_MODEL, SYSTEM_USER
from src.common.enums import WalnutSideEnum
from src.infrastructure_layer.db_readers import IWalnutImageEmbeddingReader, IWalnutReader
from src.infrastructure_layer.db_writers import IWalnutWriter
from src.infrastructure_layer.data_access_objects import (
    WalnutDAO,
    WalnutImageDAO,
    WalnutImageEmbeddingDAO,
)
from src.application_layer.services.walnut_image_loader import WalnutImageLoader
from src.application_layer.mappers.walnut__mapper import WalnutMapper


class IWalnutAL(ABC):
    @abstractmethod
    def generate_embeddings(self) -> None:
        pass

    @abstractmethod
    def create_and_save_fake_walnut(self, walnut_id: str) -> WalnutDAO:
        """Create a fake walnut with images and embeddings and save it to the database."""
        pass

    @abstractmethod
    def load_and_save_walnut_from_filesystem(self, walnut_id: str) -> WalnutDAO:
        """
        Load walnut images from filesystem, convert to domain objects,
        process and validate, then save to database.

        Args:
            walnut_id: The ID of the walnut (e.g., "0001")

        Returns:
            Saved WalnutDAO with all images and embeddings

        Raises:
            ValueError: If images are missing or invalid
            FileNotFoundError: If image directory doesn't exist
        """
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
        self.image_embedding_service: IImageEmbeddingService = image_embedding_service
        self.app_config: IAppConfig = app_config
        self.db_connection: IDatabaseConnection = db_connection
        self.walnut_image_embedding_reader: IWalnutImageEmbeddingReader = walnut_image_embedding_reader
        self.walnut_reader: IWalnutReader = walnut_reader
        self.walnut_writer: IWalnutWriter = walnut_writer
    
    def generate_embeddings(self) -> None:
        """Generate embeddings for testing purposes."""
        print(f"Image root: {self.app_config.image_root}")
        print(f"Database host: {self.app_config.database.host}")
        
        # Try to load a test image if it exists
        test_image_path = Path(self.app_config.image_root) / "0001" / "0001_B_1.jpg"
        if test_image_path.exists():
            print(f"Testing embedding generation with: {test_image_path}")
            embedding = self.image_embedding_service.generate(str(test_image_path))
            print(f"Generated embedding shape: {embedding.shape}")
        else:
            print(f"Test image not found at: {test_image_path}")
        
        # Check existing embeddings in database
        test = self.walnut_image_embedding_reader.get_by_model_name(DEFAULT_EMBEDDING_MODEL)
        print(f"Found {len(test)} embeddings in database")
        
        # Check existing walnuts in database
        walnuts = self.walnut_reader.get_all()
        print(f"Found {len(walnuts)} walnuts in database")

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
            created_by=SYSTEM_USER,
            updated_by=SYSTEM_USER,
        )

        # Create fake images for all 6 sides
        for side_enum in WalnutSideEnum:
            side = side_enum.value
            # Create fake image (now it's an ORM model)
            image = WalnutImageDAO(
                walnut_id=walnut_id,
                side=side,
                image_path=f"/images/{walnut_id}/{walnut_id}_{side[0].upper()}_1.jpg",
                width=1920,
                height=1080,
                checksum=f"fake_checksum_{walnut_id}_{side}",
                created_by=SYSTEM_USER,
                updated_by=SYSTEM_USER,
            )

            # Create fake embedding (2048-dimensional vector to match ResNet50)
            fake_embedding = np.random.rand(2048).astype(np.float32)
            embedding = WalnutImageEmbeddingDAO(
                # image_id will be set after image is saved
                model_name=DEFAULT_EMBEDDING_MODEL,
                embedding=fake_embedding,
                created_by=SYSTEM_USER,
                updated_by=SYSTEM_USER,
            )
            # Attach embedding to image - the writer will set image_id after image is saved
            image.embedding = embedding

            walnut.images.append(image)

        # Save walnut with all images and embeddings using ORM-like save
        saved_walnut = self.walnut_writer.save_with_images(walnut)
        print(f"Successfully saved walnut {walnut_id} with {len(saved_walnut.images)} images")
        return saved_walnut

    def load_and_save_walnut_from_filesystem(self, walnut_id: str) -> WalnutDAO:
        """
        Load walnut images from filesystem, convert to domain objects,
        process and validate, then save to database.

        Flow: DTO -> Domain Entity -> DAO -> Save to DB

        Args:
            walnut_id: The ID of the walnut (e.g., "0001")

        Returns:
            Saved WalnutDAO with all images

        Raises:
            ValueError: If images are missing or invalid
            FileNotFoundError: If image directory doesn't exist
        """
        # Step 1: Load images from filesystem and create DTOs
        image_root = Path(self.app_config.image_root)
        image_directory = image_root / walnut_id

        if not image_directory.exists():
            raise FileNotFoundError(f"Image directory not found: {image_directory}")

        walnut_dto = WalnutImageLoader.load_walnut_from_directory(
            walnut_id, image_directory
        )
        if walnut_dto is None:
            raise ValueError(
                f"No valid images found in directory: {image_directory}"
            )

        print(f"Loaded {len(walnut_dto.images)} images from {image_directory}")

        # Step 2: Convert DTO to Domain Entity (with validation)
        walnut_entity = WalnutMapper.dto_to_entity(walnut_dto)
        print("Converted DTO to domain entity")

        # Step 3: Domain processing and validation
        walnut_entity.validate()
        print("Domain validation passed")

        # Step 4: Generate embeddings for all images
        for side_enum in WalnutSideEnum:
            image_vo = getattr(walnut_entity, side_enum.value)
            embedding = self.image_embedding_service.generate(image_vo.path)
            walnut_entity.set_embedding(side_enum.value, embedding)
            print(f"Generated embedding for {side_enum.value} side")

        # Step 5: Convert Domain Entity to DAO
        walnut_dao = WalnutMapper.entity_to_dao(
            walnut_entity,
            walnut_id=walnut_id,
            description=f"Walnut {walnut_id} loaded from filesystem",
            created_by=SYSTEM_USER,
            updated_by=SYSTEM_USER,
            model_name=DEFAULT_EMBEDDING_MODEL,
        )
        print("Converted domain entity to DAO")

        # Step 6: Save to database
        saved_walnut = self.walnut_writer.save_with_images(walnut_dao)
        print(
            f"Successfully saved walnut {walnut_id} with {len(saved_walnut.images)} images"
        )
        return saved_walnut

