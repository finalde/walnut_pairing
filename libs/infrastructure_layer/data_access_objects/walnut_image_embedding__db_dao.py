# infrastructure_layer/data_access_objects/walnut_image_embedding__db_dao.py
"""SQLAlchemy ORM model for walnut_image_embedding table."""
from datetime import datetime
from sqlalchemy import String, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from typing import TYPE_CHECKING, Any, Optional
import numpy as np

from .base import Base
from common.constants import TABLE_WALNUT_IMAGE

if TYPE_CHECKING:
    from .walnut_image__db_dao import WalnutImageDBDAO


class WalnutImageEmbeddingDBDAO(Base):
    """Data Access Object / ORM model for the walnut_image_embedding table."""
    __tablename__ = "walnut_image_embedding"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    image_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey(f"{TABLE_WALNUT_IMAGE}.id", ondelete="CASCADE"),
        nullable=False
    )
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    embedding: Mapped[Any] = mapped_column(Vector(2048), nullable=False)  # pgvector Vector type (ResNet50 produces 2048-dim embeddings)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="NOW()")
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="NOW()")
    updated_by: Mapped[str] = mapped_column(String, nullable=False)

    def __init__(self, **kwargs):
        # Remove id from kwargs if it's None (for new objects)
        # SQLAlchemy will generate it automatically for autoincrement columns
        if 'id' in kwargs and kwargs['id'] is None:
            del kwargs['id']
        # Remove image_id if it's 0 or None (will be set after image is saved)
        if 'image_id' in kwargs and (kwargs['image_id'] == 0 or kwargs['image_id'] is None):
            del kwargs['image_id']
        super().__init__(**kwargs)

    # Relationships
    # Using string literal - SQLAlchemy resolves it by class name at runtime
    image: Mapped["WalnutImageDBDAO"] = relationship(
        "WalnutImageDBDAO",
        back_populates="embedding"
    )
