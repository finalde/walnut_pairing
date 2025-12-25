from abc import ABC, abstractmethod

from src.domain_layers.services.embedding_service import (
    IImageEmbeddingService,
)
from src.common.app_config import AppConfig  # pyright: ignore[reportMissingImports]


class IWalnutBL(ABC):
    @abstractmethod
    def generate_embeddings(self) -> None:
        pass



class WalnutBL(IWalnutBL):
    def __init__(
        self,
        image_embedding_service: IImageEmbeddingService,
        app_config: AppConfig,
    ) -> None:
        self.image_embedding_service = image_embedding_service
        self.app_config = app_config

    def generate_embeddings(self) -> None:
        print(self.app_config.image_root)
        image = f"{self.app_config.image_root}/0001/0001_B_1.jpg"
        print (image)
        embedding = self.image_embedding_service.generate(image)
        print(embedding)
