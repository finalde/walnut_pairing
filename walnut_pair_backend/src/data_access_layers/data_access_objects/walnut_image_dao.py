# src/data_access_layers/data_access_objects/walnut_image_dao.py
"""SQLAlchemy ORM model for walnut_image table."""
from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from .base import Base

if TYPE_CHECKING:
    from .walnut_dao import WalnutDAO
    from .walnut_image_embedding_dao import WalnutImageEmbeddingDAO


class WalnutImageDAO(Base):
    """Data Access Object / ORM model for the walnut_image table."""
    __tablename__ = "walnut_image"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    walnut_id: Mapped[str] = mapped_column(String, ForeignKey("walnut.id", ondelete="CASCADE"), nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)
    image_path: Mapped[str] = mapped_column(String, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="NOW()")
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="NOW()")
    updated_by: Mapped[str] = mapped_column(String, nullable=False)

    def __init__(self, **kwargs):
        # Remove id from kwargs if it's None or not provided (for new objects)
        # SQLAlchemy will generate it automatically for autoincrement columns
        if 'id' in kwargs:
            if kwargs['id'] is None:
                del kwargs['id']
            # If id is provided and not None, keep it (for existing objects from readers)
        super().__init__(**kwargs)

    # Unique constraint
    __table_args__ = (
        UniqueConstraint("walnut_id", "side", name="uq_walnut_side"),
    )

    # Relationships
    walnut: Mapped["WalnutDAO"] = relationship("WalnutDAO", back_populates="images")
    embedding: Mapped[Optional["WalnutImageEmbeddingDAO"]] = relationship(
        "WalnutImageEmbeddingDAO",
        back_populates="image",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="select"
    )
