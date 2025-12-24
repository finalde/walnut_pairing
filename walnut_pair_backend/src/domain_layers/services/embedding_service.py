import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

from abc import ABC, abstractmethod
from typing import Optional, Union
import numpy as np


class IImageEmbeddingService(ABC):
    @abstractmethod
    def generate(self, data: Union[str, Image.Image]) -> np.ndarray:
        """
        Generate embedding from input data.
        `data` can be an image path (str) or a PIL.Image.Image.
        """
        pass


class ImageEmbeddingService(IImageEmbeddingService):
    model: nn.Module
    preprocess: transforms.Compose
    device: str

    def __init__(self, device: Optional[str] = None) -> None:
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        # Pretrained ResNet50 without classifier
        resnet = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
        self.model = nn.Sequential(*list(resnet.children())[:-1])  # remove final FC
        self.model.eval().to(self.device)

        # Image preprocessing
        self.preprocess = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
        ])

    def generate(self, data: Union[str, Image.Image]) -> np.ndarray:
        if isinstance(data, str):
            img = Image.open(data).convert("RGB")
        elif isinstance(data, Image.Image):
            img = data.convert("RGB")
        else:
            raise TypeError(f"Unsupported input type: {type(data)}")

        x: torch.Tensor = self.preprocess(img).unsqueeze(0).to(self.device)
        with torch.no_grad():
            embedding: torch.Tensor = self.model(x).squeeze().cpu()
        return embedding.numpy()
