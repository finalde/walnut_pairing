# domain_layer/domain_services/embedding__domain_service.py
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms


class ImageEmbeddingDomainService:
    @staticmethod
    def generate(image_path: str) -> np.ndarray:
        device: str = "cuda" if torch.cuda.is_available() else "cpu"

        resnet = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
        model: nn.Module = nn.Sequential(*list(resnet.children())[:-1])
        model.eval().to(device)

        preprocess: transforms.Compose = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

        img = Image.open(image_path).convert("RGB")
        x: torch.Tensor = preprocess(img).unsqueeze(0).to(device)
        with torch.no_grad():
            embedding: torch.Tensor = model(x).squeeze().cpu()
        return embedding.numpy()

