from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

from src.domain_layers.services.embedding_service import (
    IImageEmbeddingService,
)
from src.common.interfaces import IAppConfig, IDatabaseConnection
from src.data_access_layers.db_readers import WalnutImageEmbeddingReader, WalnutReader  # pyright: ignore[reportMissingImports]
from src.data_access_layers.db_readers import WalnutReader

class IWalnutBL(ABC):
    @abstractmethod
    def generate_embeddings(self) -> None:
        pass



class WalnutBL(IWalnutBL):
    def __init__(
        self,
        image_embedding_service: IImageEmbeddingService,
        app_config: IAppConfig,
        db_connection: IDatabaseConnection,
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

