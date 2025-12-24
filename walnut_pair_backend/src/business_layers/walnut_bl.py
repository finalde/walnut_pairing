from abc import ABC, abstractmethod
from typing import Any
from src.domain_layers.services.embedding_service import IImageEmbeddingService, ImageEmbeddingService
import numpy as np

from src.common.app_config import AppConfig  # pyright: ignore[reportMissingImports]

class IWalnutBL(ABC):
    @abstractmethod
    def run(self):
        pass

class WalnutBL:
    def __init__(self, image_embedding_service: IImageEmbeddingService, app_config: AppConfig):
        self.image_embedding_service = image_embedding_service
        self.app_config = app_config

    def generate_embeddings(self):
        image_path: str = "/home/dalu/images/walnut_B.jpg"
        pass
