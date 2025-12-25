from abc import ABC, abstractmethod
from typing import Optional
import psycopg2

from src.domain_layers.services.embedding_service import (
    IImageEmbeddingService,
)
from src.common.app_config import AppConfig
from src.data_access_layers.db_readers import WalnutImageEmbeddingReader  # pyright: ignore[reportMissingImports]


class IWalnutBL(ABC):
    @abstractmethod
    def generate_embeddings(self) -> None:
        pass



class WalnutBL(IWalnutBL):
    def __init__(
        self,
        image_embedding_service: IImageEmbeddingService,
        app_config: AppConfig,
        db_connection: psycopg2.extensions.connection
    ) -> None:  
        self.image_embedding_service = image_embedding_service
        self.app_config = app_config
        self.db_connection = db_connection
    def generate_embeddings(self) -> None:
        print(self.app_config.image_root)
        image = f"{self.app_config.image_root}/0001/0001_B_1.jpg"
        print(self.app_config.database.host)
        embedding = self.image_embedding_service.generate(image)
        walnut_image_embedding_reader = WalnutImageEmbeddingReader(self.db_connection)
        test = walnut_image_embedding_reader.get_by_model_name("resnet50-imagenet")
        print(f"Found {len(test)} embeddings")

