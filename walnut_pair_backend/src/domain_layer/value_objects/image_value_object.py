# src/domain_layer/value_objects/image_value_object.py
from dataclasses import dataclass
from PIL import Image
from src.common.enums import WalnutSideEnum
from src.common.constants import UNKNOWN_IMAGE_FORMAT


@dataclass(frozen=True)
class ImageValueObject:
    side: WalnutSideEnum
    path: str  # path to image
    width: int
    height: int
    format: str  # e.g., JPEG, PNG
    hash: str  # optional, for image identity/checksum

    @classmethod
    def from_path(cls, path: str, side: WalnutSideEnum) -> "ImageValueObject":
        img = Image.open(path)
        img_hash = str(hash(img.tobytes()))
        img_format = img.format or UNKNOWN_IMAGE_FORMAT
        return cls(
            side=side,
            path=path,
            width=img.width,
            height=img.height,
            format=img_format,
            hash=img_hash
        )
