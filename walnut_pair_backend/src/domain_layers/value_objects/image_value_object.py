# src/domain_layers/value_objects/image_value_object.py
from dataclasses import dataclass
from enum import Enum
from PIL import Image
from src.common.enums import WalnutSideEnum

@dataclass(frozen=True)
class ImageValueObject:
    side: WalnutSideEnum
    path: str  # path to image
    width: int
    height: int
    format: str  # e.g., JPEG, PNG
    hash: str  # optional, for image identity/checksum

    @classmethod
    def from_path(cls, path: str, side: WalnutSideEnum):
        img = Image.open(path)
        img_hash = str(hash(img.tobytes()))
        return cls(
            side=side,
            path=path,
            width=img.width,
            height=img.height,
            format=img.format,
            hash=img_hash
        )
