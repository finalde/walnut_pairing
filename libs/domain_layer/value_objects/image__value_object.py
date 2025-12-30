# domain_layer/value_objects/image__value_object.py
from dataclasses import dataclass

from common.constants import UNKNOWN_IMAGE_FORMAT
from common.enums import WalnutSideEnum
from PIL import Image


@dataclass(frozen=True)
class ImageValueObject:
    side: WalnutSideEnum
    path: str
    width: int
    height: int
    format: str
    hash: str
    camera_distance_mm: float 

    @classmethod
    def from_path(cls, path: str, side: WalnutSideEnum, camera_distance_mm: float) -> "ImageValueObject":
        img = Image.open(path)
        img_hash = str(hash(img.tobytes()))
        img_format = img.format or UNKNOWN_IMAGE_FORMAT
        return cls(side=side, path=path, width=img.width, height=img.height, format=img_format, hash=img_hash, camera_distance_mm=camera_distance_mm)
