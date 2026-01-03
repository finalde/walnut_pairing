# infrastructure_layer/db_writers/walnut_comparison__db_writer.py
from abc import ABC, abstractmethod
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure_layer.data_access_objects.walnut_comparison__db_dao import WalnutComparisonDBDAO


class IWalnutComparisonDBWriter(ABC):
    """Interface for writing walnut comparisons to database."""

    @abstractmethod
    async def save_async(self, comparison_dao: WalnutComparisonDBDAO) -> WalnutComparisonDBDAO:
        """Save a new walnut comparison to the database."""
        pass

    @abstractmethod
    async def save_or_update_async(self, comparison_dao: WalnutComparisonDBDAO) -> WalnutComparisonDBDAO:
        """Save or update a walnut comparison (upsert operation)."""
        pass

    @abstractmethod
    async def bulk_save_or_update_async(self, comparison_daos: List[WalnutComparisonDBDAO]) -> List[WalnutComparisonDBDAO]:
        """Bulk save or update walnut comparisons (upsert operation)."""
        pass


class WalnutComparisonDBWriter(IWalnutComparisonDBWriter):
    """Implementation for writing walnut comparisons to database."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize with an async SQLAlchemy session.
        
        Args:
            session: AsyncSession instance (injected via DI container)
        """
        self.session: AsyncSession = session

    async def save_async(self, comparison_dao: WalnutComparisonDBDAO) -> WalnutComparisonDBDAO:
        """Save a new walnut comparison to the database."""
        self.session.add(comparison_dao)
        await self.session.commit()
        await self.session.refresh(comparison_dao)
        return comparison_dao

    async def save_or_update_async(self, comparison_dao: WalnutComparisonDBDAO) -> WalnutComparisonDBDAO:
        """Save or update a walnut comparison (upsert operation)."""
        # Try to find existing comparison
        result = await self.session.execute(
            select(WalnutComparisonDBDAO)
            .where(
                WalnutComparisonDBDAO.walnut_id == comparison_dao.walnut_id,
                WalnutComparisonDBDAO.compared_walnut_id == comparison_dao.compared_walnut_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing
            existing.width_diff_mm = comparison_dao.width_diff_mm
            existing.height_diff_mm = comparison_dao.height_diff_mm
            existing.thickness_diff_mm = comparison_dao.thickness_diff_mm
            existing.basic_similarity = comparison_dao.basic_similarity
            existing.width_weight = comparison_dao.width_weight
            existing.height_weight = comparison_dao.height_weight
            existing.thickness_weight = comparison_dao.thickness_weight
            existing.front_embedding_score = comparison_dao.front_embedding_score
            existing.back_embedding_score = comparison_dao.back_embedding_score
            existing.left_embedding_score = comparison_dao.left_embedding_score
            existing.right_embedding_score = comparison_dao.right_embedding_score
            existing.top_embedding_score = comparison_dao.top_embedding_score
            existing.down_embedding_score = comparison_dao.down_embedding_score
            existing.advanced_similarity = comparison_dao.advanced_similarity
            existing.final_similarity = comparison_dao.final_similarity
            existing.updated_by = comparison_dao.updated_by
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            # Insert new
            self.session.add(comparison_dao)
            await self.session.commit()
            await self.session.refresh(comparison_dao)
            return comparison_dao

    async def bulk_save_or_update_async(self, comparison_daos: List[WalnutComparisonDBDAO]) -> List[WalnutComparisonDBDAO]:
        """Bulk save or update walnut comparisons (upsert operation)."""
        saved_comparisons: List[WalnutComparisonDBDAO] = []

        for comparison_dao in comparison_daos:
            # Try to find existing comparison
            result = await self.session.execute(
                select(WalnutComparisonDBDAO)
                .where(
                    WalnutComparisonDBDAO.walnut_id == comparison_dao.walnut_id,
                    WalnutComparisonDBDAO.compared_walnut_id == comparison_dao.compared_walnut_id,
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing
                existing.width_diff_mm = comparison_dao.width_diff_mm
                existing.height_diff_mm = comparison_dao.height_diff_mm
                existing.thickness_diff_mm = comparison_dao.thickness_diff_mm
                existing.basic_similarity = comparison_dao.basic_similarity
                existing.width_weight = comparison_dao.width_weight
                existing.height_weight = comparison_dao.height_weight
                existing.thickness_weight = comparison_dao.thickness_weight
                existing.front_embedding_score = comparison_dao.front_embedding_score
                existing.back_embedding_score = comparison_dao.back_embedding_score
                existing.left_embedding_score = comparison_dao.left_embedding_score
                existing.right_embedding_score = comparison_dao.right_embedding_score
                existing.top_embedding_score = comparison_dao.top_embedding_score
                existing.down_embedding_score = comparison_dao.down_embedding_score
                existing.advanced_similarity = comparison_dao.advanced_similarity
                existing.final_similarity = comparison_dao.final_similarity
                existing.updated_by = comparison_dao.updated_by
                saved_comparisons.append(existing)
            else:
                # Insert new
                self.session.add(comparison_dao)
                saved_comparisons.append(comparison_dao)

        # Commit all changes at once
        await self.session.commit()

        # Refresh all saved comparisons
        for comparison in saved_comparisons:
            await self.session.refresh(comparison)

        return saved_comparisons

