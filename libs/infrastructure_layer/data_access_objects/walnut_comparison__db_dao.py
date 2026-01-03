# infrastructure_layer/data_access_objects/walnut_comparison__db_dao.py
"""SQLAlchemy ORM model for walnut_comparison table."""
from datetime import datetime
from typing import TYPE_CHECKING

from typing import Optional

from common.constants import CONSTRAINT_UQ_WALNUT_COMPARISON, TABLE_WALNUT
from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base__db_dao import Base

if TYPE_CHECKING:
    pass


class WalnutComparisonDBDAO(Base):
    """Data Access Object / ORM model for the walnut_comparison table."""

    __tablename__ = "walnut_comparison"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    walnut_id: Mapped[str] = mapped_column(String, ForeignKey(f"{TABLE_WALNUT}.id", ondelete="CASCADE"), nullable=False)
    compared_walnut_id: Mapped[str] = mapped_column(String, ForeignKey(f"{TABLE_WALNUT}.id", ondelete="CASCADE"), nullable=False)
    # Basic similarity metrics
    width_diff_mm: Mapped[float] = mapped_column(Float, nullable=False)
    height_diff_mm: Mapped[float] = mapped_column(Float, nullable=False)
    thickness_diff_mm: Mapped[float] = mapped_column(Float, nullable=False)
    basic_similarity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    width_weight: Mapped[float] = mapped_column(Float, nullable=False)
    height_weight: Mapped[float] = mapped_column(Float, nullable=False)
    thickness_weight: Mapped[float] = mapped_column(Float, nullable=False)
    # Advanced similarity metrics (embedding scores)
    front_embedding_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    back_embedding_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    left_embedding_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    right_embedding_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    top_embedding_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    down_embedding_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    advanced_similarity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # Final combined similarity
    final_similarity: Mapped[float] = mapped_column(Float, nullable=False)
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="NOW()")
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default="NOW()")
    updated_by: Mapped[str] = mapped_column(String, nullable=False)

    def __init__(self, **kwargs):
        # Remove id from kwargs if it's None or not provided (for new objects)
        if "id" in kwargs:
            if kwargs["id"] is None:
                del kwargs["id"]
        super().__init__(**kwargs)

    # Unique constraint
    __table_args__ = (UniqueConstraint("walnut_id", "compared_walnut_id", name=CONSTRAINT_UQ_WALNUT_COMPARISON),)

