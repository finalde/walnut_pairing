# application_layer/dtos/walnut_comparison__dto.py
"""DTOs for walnut comparison/pairing results."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class WalnutComparisonDTO(BaseModel):
    """Data Transfer Object for walnut comparison/pairing result."""

    id: int
    walnut_id: str
    compared_walnut_id: str
    width_diff_mm: float
    height_diff_mm: float
    thickness_diff_mm: float
    basic_similarity: Optional[float]
    advanced_similarity: Optional[float]
    final_similarity: float
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""
        from_attributes = True

