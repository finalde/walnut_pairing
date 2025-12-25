# src/data_access_layers/data_access_objects/walnut_image_dao.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from walnut_image_embedding_dao import (
    WalnutImageEmbeddingDAO,
)


@dataclass
class WalnutImageDAO:
    """
    Data Access Object for the walnut_image table.
    Represents a walnut image record in the database.
    """
    id: Optional[int] = None  # BIGSERIAL, auto-generated
    walnut_id: str = ""
    side: str = ""
    image_path: str = ""
    width: int = 0
    height: int = 0
    checksum: str = ""
    created_at: Optional[datetime] = None  # NOT NULL in DB, set by DEFAULT NOW()
    created_by: str = ""
    updated_at: Optional[datetime] = None  # NOT NULL in DB, set by DEFAULT NOW()
    updated_by: str = ""
    embedding: Optional["WalnutImageEmbeddingDAO"] = None  # One-to-one relationship

