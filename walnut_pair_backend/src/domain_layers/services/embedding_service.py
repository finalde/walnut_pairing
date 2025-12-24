import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

from abc import ABC, abstractmethod
from typing import Any

class IImageEmbeddingService(ABC):
    @abstractmethod
    def generate(self, data: Any):
        """
        Generate embedding from input data.
        data can be an image path or PIL.Image or other types depending on implementation.
        """
        pass

class ImageEmbeddingService(IImageEmbeddingService):
    def __init__(self, device: str = None):
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

    def generate(self, image_path: str):
        img = Image.open(image_path).convert("RGB")
        x = self.preprocess(img).unsqueeze(0).to(self.device)
        with torch.no_grad():
            embedding = self.model(x).squeeze().cpu()
        return embedding.numpy()  # 2048-dim vector
