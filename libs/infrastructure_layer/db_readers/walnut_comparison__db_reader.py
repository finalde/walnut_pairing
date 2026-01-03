# infrastructure_layer/db_readers/walnut_comparison__db_reader.py
"""Database reader for walnut comparisons."""
from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..data_access_objects.walnut_comparison__db_dao import WalnutComparisonDBDAO


class IWalnutComparisonDBReader(ABC):
    """Interface for reading walnut comparison data from database."""

    @abstractmethod
    async def get_all_async(self) -> List[WalnutComparisonDBDAO]:
        """Get all walnut comparisons from the database."""
        pass

    @abstractmethod
    async def get_by_walnut_id_async(self, walnut_id: str) -> List[WalnutComparisonDBDAO]:
        """Get all comparisons for a specific walnut."""
        pass

    @abstractmethod
    async def get_by_ids_async(self, walnut_id: str, compared_walnut_id: str) -> Optional[WalnutComparisonDBDAO]:
        """Get a specific comparison between two walnuts."""
        pass


class WalnutComparisonDBReader(IWalnutComparisonDBReader):
    """Implementation of IWalnutComparisonDBReader for reading walnut comparison data from PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the reader with an async session.

        Args:
            session: AsyncSession instance (injected via DI container)
        """
        self.session: AsyncSession = session

    async def get_all_async(self) -> List[WalnutComparisonDBDAO]:
        """Get all walnut comparisons from the database."""
        result = await self.session.execute(
            select(WalnutComparisonDBDAO).order_by(WalnutComparisonDBDAO.final_similarity.desc())
        )
        return list(result.scalars().all())

    async def get_by_walnut_id_async(self, walnut_id: str) -> List[WalnutComparisonDBDAO]:
        """Get all comparisons for a specific walnut."""
        result = await self.session.execute(
            select(WalnutComparisonDBDAO)
            .where(
                (WalnutComparisonDBDAO.walnut_id == walnut_id) | 
                (WalnutComparisonDBDAO.compared_walnut_id == walnut_id)
            )
            .order_by(WalnutComparisonDBDAO.final_similarity.desc())
        )
        return list(result.scalars().all())

    async def get_by_ids_async(self, walnut_id: str, compared_walnut_id: str) -> Optional[WalnutComparisonDBDAO]:
        """Get a specific comparison between two walnuts."""
        result = await self.session.execute(
            select(WalnutComparisonDBDAO)
            .where(
                (WalnutComparisonDBDAO.walnut_id == walnut_id) &
                (WalnutComparisonDBDAO.compared_walnut_id == compared_walnut_id)
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

