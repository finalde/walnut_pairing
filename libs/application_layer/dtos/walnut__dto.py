# application_layer/dtos/walnut__dto.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class WalnutImageDTO:
    image_id: int
    walnut_id: str
    side: str
    image_path: str
    width: int
    height: int
    checksum: str
    embedding_id: Optional[int] = None


@dataclass
class WalnutDTO:
    walnut_id: str
    description: str
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    length_mm: Optional[float] = None
    width_mm: Optional[float] = None
    height_mm: Optional[float] = None
    images: List[WalnutImageDTO] = None

    def __post_init__(self) -> None:
        if self.images is None:
            self.images = []
