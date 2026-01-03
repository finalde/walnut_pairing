# infrastructure_layer/db_readers/walnut_image__db_reader.py
"""Database reader for walnut images."""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..data_access_objects import WalnutImageDBDAO

if TYPE_CHECKING:
    from .walnut_image_embedding__db_reader import IWalnutImageEmbeddingDBReader


class IWalnutImageDBReader(ABC):
    """Interface for reading walnut image data from database."""

    @abstractmethod
    async def get_by_id_async(self, image_id: int) -> Optional[WalnutImageDBDAO]:
        """Get a walnut image by its ID without embedding."""
        pass

    @abstractmethod
    async def get_by_walnut_id_async(self, walnut_id: str) -> List[WalnutImageDBDAO]:
        """Get all images for a specific walnut without embeddings."""
        pass

    @abstractmethod
    async def get_by_walnut_id_with_embeddings_async(self, walnut_id: str) -> List[WalnutImageDBDAO]:
        """Get all images for a specific walnut with their embeddings loaded."""
        pass

    @abstractmethod
    async def get_by_id_with_embedding_async(self, image_id: int) -> Optional[WalnutImageDBDAO]:
        """Get a walnut image by ID with its embedding loaded."""
        pass


class WalnutImageDBReader(IWalnutImageDBReader):
    """Implementation of IWalnutImageDBReader for reading walnut image data from PostgreSQL."""

    def __init__(
        self,
        session: AsyncSession,
        embedding_reader: "IWalnutImageEmbeddingDBReader",
    ) -> None:
        """
        Initialize the reader with an async session and embedding reader.

        Args:
            session: AsyncSession instance (injected via DI container)
            embedding_reader: IWalnutImageEmbeddingDBReader instance (injected via DI container).
        """
        self.session: AsyncSession = session
        self.embedding_reader: "IWalnutImageEmbeddingDBReader" = embedding_reader

    async def get_by_id_async(self, image_id: int) -> Optional[WalnutImageDBDAO]:
        """Get a walnut image by its ID without embedding."""
        result = await self.session.execute(
            select(WalnutImageDBDAO).where(WalnutImageDBDAO.id == image_id)
        )
        return result.scalar_one_or_none()

    async def get_by_walnut_id_async(self, walnut_id: str) -> List[WalnutImageDBDAO]:
        """Get all images for a specific walnut without embeddings."""
        result = await self.session.execute(
            select(WalnutImageDBDAO)
            .where(WalnutImageDBDAO.walnut_id == walnut_id)
            .order_by(WalnutImageDBDAO.side)
        )
        return list(result.scalars().all())

    async def get_by_walnut_id_with_embeddings_async(self, walnut_id: str) -> List[WalnutImageDBDAO]:
        """Get all images for a specific walnut with their embeddings loaded."""
        images = await self.get_by_walnut_id_async(walnut_id)

        # Load embeddings for each image
        for image in images:
            if image.id is not None:
                image.embedding = await self.embedding_reader.get_by_image_id_async(image.id)

        return images

    async def get_by_id_with_embedding_async(self, image_id: int) -> Optional[WalnutImageDBDAO]:
        """Get a walnut image by ID with its embedding loaded."""
        image = await self.get_by_id_async(image_id)
        if image is None:
            return None

        # Load embedding
        if image.id is not None:
            image.embedding = await self.embedding_reader.get_by_image_id_async(image.id)

        return image
