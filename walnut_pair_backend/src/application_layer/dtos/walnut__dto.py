# src/application_layer/dtos/walnut__dto.py
"""Data Transfer Objects for walnut data - no domain knowledge."""
from dataclasses import dataclass
from typing import List
from pathlib import Path


@dataclass
class WalnutImageDTO:
    """DTO for walnut image data loaded from filesystem."""
    file_path: Path
    side_letter: str  # F, B, L, R, T, D
    width: int
    height: int
    file_size: int
    checksum: str  # File hash/checksum


@dataclass
class WalnutDTO:
    """DTO for walnut data loaded from filesystem."""
    walnut_id: str
    image_directory: Path
    images: List[WalnutImageDTO]

