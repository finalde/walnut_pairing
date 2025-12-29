# application_layer/dtos/walnut__create_dto.py
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class WalnutImageCreateDTO:
    side: str
    image_path: str
    width: int
    height: int
    checksum: str


@dataclass
class WalnutCreateDTO:
    description: Optional[str] = None
    images: List[WalnutImageCreateDTO] = None

    def __post_init__(self) -> None:
        if self.images is None:
            self.images = []

