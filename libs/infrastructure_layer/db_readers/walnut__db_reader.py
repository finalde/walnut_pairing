# infrastructure_layer/db_readers/walnut__reader.py
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..data_access_objects import WalnutDBDAO

if TYPE_CHECKING:
    from .walnut_image__db_reader import IWalnutImageDBReader


class IWalnutDBReader(ABC):
    """Interface for reading walnut data from the database."""

    @abstractmethod
    async def get_by_id_async(self, walnut_id: str) -> Optional[WalnutDBDAO]:
        """Get a walnut by its ID with related images and embeddings loaded."""
        pass

    @abstractmethod
    async def get_all_async(self) -> List[WalnutDBDAO]:
        """Get all walnuts from the database with related images and embeddings loaded."""
        pass

    @abstractmethod
    async def get_by_id_with_images_async(self, walnut_id: str) -> Optional[WalnutDBDAO]:
        """Get a walnut by ID with its related images and embeddings loaded.

        Note: This method now delegates to get_by_id_async() which already loads
        images and embeddings. Kept for backward compatibility.
        """
        pass


class WalnutDBReader(IWalnutDBReader):
    """Implementation of IWalnutDBReader for reading walnut data from PostgreSQL."""

    def __init__(
        self,
        session: AsyncSession,
        image_reader: "IWalnutImageDBReader",
    ) -> None:
        """
        Initialize the reader with an async session and image reader.

        Args:
            session: AsyncSession instance (injected via DI container)
            image_reader: IWalnutImageDBReader instance (injected via DI container).
        """
        self.session: AsyncSession = session
        self.image_reader: "IWalnutImageDBReader" = image_reader

    async def get_by_id_async(self, walnut_id: str) -> Optional[WalnutDBDAO]:
        """Get a walnut by its ID with related images and embeddings loaded."""
        from ..data_access_objects.walnut_image__db_dao import WalnutImageDBDAO
        
        result = await self.session.execute(
            select(WalnutDBDAO)
            .options(
                selectinload(WalnutDBDAO.images).selectinload(WalnutImageDBDAO.embedding)
            )
            .where(WalnutDBDAO.id == walnut_id)
        )
        walnut = result.scalar_one_or_none()
        
        if walnut is not None:
            # Explicitly access relationships to ensure they're loaded while in async context
            _ = walnut.images
            for image in walnut.images:
                _ = image.embedding
        
        return walnut

    async def get_all_async(self) -> List[WalnutDBDAO]:
        """Get all walnuts from the database with related images and embeddings loaded."""
        from ..data_access_objects.walnut_image__db_dao import WalnutImageDBDAO
        
        result = await self.session.execute(
            select(WalnutDBDAO)
            .options(
                selectinload(WalnutDBDAO.images).selectinload(WalnutImageDBDAO.embedding)
            )
            .order_by(WalnutDBDAO.created_at.desc())
        )
        walnuts = result.scalars().all()

        # Explicitly access relationships to ensure they're loaded while in async context
        for walnut in walnuts:
            _ = walnut.images
            for image in walnut.images:
                _ = image.embedding

        return list(walnuts)

    async def get_by_id_with_images_async(self, walnut_id: str) -> Optional[WalnutDBDAO]:
        """Get a walnut by ID with its related images and embeddings loaded.

        Note: This method now delegates to get_by_id_async() which already loads
        images and embeddings. Kept for backward compatibility.
        """
        return await self.get_by_id_async(walnut_id)
