# src/infrastructure_layer/data_access_objects/walnut__file_dao.py
"""File Data Access Objects for walnut data loaded from filesystem - no domain knowledge."""
from dataclasses import dataclass
from typing import List
from pathlib import Path


@dataclass
class WalnutImageFileDAO:
    """File DAO for walnut image data loaded from filesystem."""
    file_path: Path
    side_letter: str  # F, B, L, R, T, D
    width: int
    height: int
    file_size: int
    checksum: str  # File hash/checksum


@dataclass
class WalnutFileDAO:
    """File DAO for walnut data loaded from filesystem."""
    walnut_id: str
    image_directory: Path
    images: List[WalnutImageFileDAO]

