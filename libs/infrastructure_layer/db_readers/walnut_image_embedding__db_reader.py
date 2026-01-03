# infrastructure_layer/db_readers/walnut_image_embedding__db_reader.py
from abc import ABC, abstractmethod
from typing import List, Optional

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure_layer.data_access_objects.walnut_image_embedding__db_dao import (
    WalnutImageEmbeddingDBDAO,
)


class IWalnutImageEmbeddingDBReader(ABC):
    """Interface for reading walnut image embedding data from the database."""

    @abstractmethod
    async def get_by_id_async(self, embedding_id: int) -> Optional[WalnutImageEmbeddingDBDAO]:
        """Get an embedding by its ID."""
        pass

    @abstractmethod
    async def get_by_image_id_async(self, image_id: int) -> Optional[WalnutImageEmbeddingDBDAO]:
        """Get an embedding by image ID (one-to-one relationship)."""
        pass

    @abstractmethod
    async def get_by_model_name_async(self, model_name: str) -> List[WalnutImageEmbeddingDBDAO]:
        """Get all embeddings for a specific model."""
        pass


class WalnutImageEmbeddingDBReader(IWalnutImageEmbeddingDBReader):
    """Implementation of IWalnutImageEmbeddingDBReader for reading embedding data from PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the reader with an async session.

        Args:
            session: AsyncSession instance (injected via DI container)
        """
        self.session: AsyncSession = session

    def _vector_to_numpy(self, vector_data) -> np.ndarray:
        """
        Convert PostgreSQL vector type to numpy array.

        Args:
            vector_data: Vector data from PostgreSQL (could be string, list, or array)

        Returns:
            numpy.ndarray: The embedding as a numpy array
        """
        if isinstance(vector_data, str):
            # If it's a string like '[0.1, 0.2, ...]', parse it
            import ast

            vector_list = ast.literal_eval(vector_data)
            return np.array(vector_list, dtype=np.float32)
        elif isinstance(vector_data, (list, tuple)):
            return np.array(vector_data, dtype=np.float32)
        elif isinstance(vector_data, np.ndarray):
            return vector_data.astype(np.float32)
        else:
            # Try to convert directly
            return np.array(vector_data, dtype=np.float32)

    async def get_by_id_async(self, embedding_id: int) -> Optional[WalnutImageEmbeddingDBDAO]:
        """Get an embedding by its ID."""
        result = await self.session.execute(
            select(WalnutImageEmbeddingDBDAO).where(WalnutImageEmbeddingDBDAO.id == embedding_id)
        )
        embedding = result.scalar_one_or_none()
        
        if embedding is None:
            return None

        # Convert embedding vector to numpy if needed
        if embedding.embedding is not None and not isinstance(embedding.embedding, np.ndarray):
            embedding.embedding = self._vector_to_numpy(embedding.embedding)

        return embedding

    async def get_by_image_id_async(self, image_id: int) -> Optional[WalnutImageEmbeddingDBDAO]:
        """Get an embedding by image ID (one-to-one relationship)."""
        result = await self.session.execute(
            select(WalnutImageEmbeddingDBDAO)
            .where(WalnutImageEmbeddingDBDAO.image_id == image_id)
            .limit(1)
        )
        embedding = result.scalar_one_or_none()
        
        if embedding is None:
            return None

        # Convert embedding vector to numpy if needed
        if embedding.embedding is not None and not isinstance(embedding.embedding, np.ndarray):
            embedding.embedding = self._vector_to_numpy(embedding.embedding)

        return embedding

    async def get_by_model_name_async(self, model_name: str) -> List[WalnutImageEmbeddingDBDAO]:
        """Get all embeddings for a specific model."""
        result = await self.session.execute(
            select(WalnutImageEmbeddingDBDAO)
            .where(WalnutImageEmbeddingDBDAO.model_name == model_name)
            .order_by(WalnutImageEmbeddingDBDAO.created_at.desc())
        )
        embeddings = result.scalars().all()
        
        # Convert embedding vectors to numpy if needed
        for embedding in embeddings:
            if embedding.embedding is not None and not isinstance(embedding.embedding, np.ndarray):
                embedding.embedding = self._vector_to_numpy(embedding.embedding)

        return list(embeddings)
