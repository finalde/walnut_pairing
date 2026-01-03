# infrastructure_layer/db_writers/walnut_image_embedding__db_writer.py
from abc import ABC, abstractmethod

import numpy as np
from infrastructure_layer.data_access_objects import WalnutImageEmbeddingDBDAO
from sqlalchemy.ext.asyncio import AsyncSession


class IWalnutImageEmbeddingDBWriter(ABC):
    """Interface for writing walnut image embedding data to the database."""

    @abstractmethod
    async def save_async(self, embedding: WalnutImageEmbeddingDBDAO) -> WalnutImageEmbeddingDBDAO:
        """Save an embedding to the database. Returns embedding with generated ID."""
        pass

    @abstractmethod
    async def save_or_update_async(self, embedding: WalnutImageEmbeddingDBDAO) -> WalnutImageEmbeddingDBDAO:
        """Save or update an embedding. Returns embedding with ID."""
        pass


class WalnutImageEmbeddingDBWriter(IWalnutImageEmbeddingDBWriter):
    """Implementation for writing walnut image embedding data using SQLAlchemy async ORM."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the writer with an async SQLAlchemy session.

        Args:
            session: AsyncSession instance (injected via DI container)
        """
        self.session: AsyncSession = session

    async def save_async(self, embedding: WalnutImageEmbeddingDBDAO) -> WalnutImageEmbeddingDBDAO:
        """Save an embedding to the database. Returns embedding with generated ID."""
        if embedding.embedding is None:
            raise ValueError("Embedding cannot be None")

        try:
            # Convert numpy array to list for pgvector
            if isinstance(embedding.embedding, np.ndarray):
                embedding.embedding = embedding.embedding.tolist()

            # Add to session and flush to get generated ID
            self.session.add(embedding)
            await self.session.flush()  # Flush to get the generated ID without committing
            return embedding
        except Exception:
            await self.session.rollback()
            raise

    async def save_or_update_async(self, embedding: WalnutImageEmbeddingDBDAO) -> WalnutImageEmbeddingDBDAO:
        """Save or update an embedding. Returns embedding with ID."""
        try:
            if embedding.id is not None:
                # Update existing - fetch from database
                existing = await self.session.get(WalnutImageEmbeddingDBDAO, embedding.id)
                if existing is None:
                    raise ValueError(f"Embedding with id {embedding.id} not found")

                # Update fields
                existing.model_name = embedding.model_name
                if embedding.embedding is not None:
                    if isinstance(embedding.embedding, np.ndarray):
                        existing.embedding = embedding.embedding.tolist()
                    else:
                        existing.embedding = embedding.embedding
                existing.updated_by = embedding.updated_by
                # updated_at is set by database default

                await self.session.flush()
                return existing
            else:
                # Insert new
                return await self.save_async(embedding)
        except Exception:
            await self.session.rollback()
            raise
