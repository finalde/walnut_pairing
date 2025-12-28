# src/infrastructure_layer/data_access_objects/walnut__dao.py
"""SQLAlchemy ORM model for walnut table."""
from datetime import datetime
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING

from .base import Base

if TYPE_CHECKING:
    from .walnut_image_dao import WalnutImageDAO


class WalnutDAO(Base):
    """Data Access Object / ORM model for the walnut table."""
    __tablename__ = "walnut"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="NOW()")
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="NOW()")
    updated_by: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    # Using string literal - SQLAlchemy resolves it by class name at runtime
    images: Mapped[List["WalnutImageDAO"]] = relationship(
        "WalnutImageDAO",
        back_populates="walnut",
        cascade="all, delete-orphan",
        lazy="select"
    )
