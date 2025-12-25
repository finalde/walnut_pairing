# src/data_access_layers/data_access_objects/walnut_image_embedding_dao.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import numpy as np


@dataclass
class WalnutImageEmbeddingDAO:
    """
    Data Access Object for the walnut_image_embedding table.
    Represents an embedding record for a walnut image in the database.
    """
    id: Optional[int] = None  # BIGSERIAL, auto-generated
    image_id: int = 0
    model_name: str = ""
    embedding: Optional[np.ndarray] = None  # VECTOR(512)
    created_at: Optional[datetime] = None  # NOT NULL in DB, set by DEFAULT NOW()
    created_by: str = ""
    updated_at: Optional[datetime] = None  # NOT NULL in DB, set by DEFAULT NOW()
    updated_by: str = ""

