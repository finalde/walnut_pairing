# src/data_access_layers/data_access_objects/walnut_dao.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from walnut_image_dao import WalnutImageDAO


@dataclass
class WalnutDAO:
    """
    Data Access Object for the walnut table.
    Represents a walnut record in the database.
    """
    id: str
    description: str = ""
    created_at: Optional[datetime] = None  # NOT NULL in DB, set by DEFAULT NOW()
    created_by: str = ""
    updated_at: Optional[datetime] = None  # NOT NULL in DB, set by DEFAULT NOW()
    updated_by: str = ""
    images: List["WalnutImageDAO"] = field(default_factory=list)

