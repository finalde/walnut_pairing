# src/data_access_layers/db_writers/walnut_image_embedding_writer.py
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from src.data_access_layers.data_access_objects import WalnutImageEmbeddingDAO
import numpy as np


class IWalnutImageEmbeddingWriter(ABC):
    """Interface for writing walnut image embedding data to the database."""

    @abstractmethod
    def save(self, embedding: WalnutImageEmbeddingDAO) -> WalnutImageEmbeddingDAO:
        """Save an embedding to the database. Returns embedding with generated ID."""
        pass

    @abstractmethod
    def save_or_update(self, embedding: WalnutImageEmbeddingDAO) -> WalnutImageEmbeddingDAO:
        """Save or update an embedding. Returns embedding with ID."""
        pass


class WalnutImageEmbeddingWriter(IWalnutImageEmbeddingWriter):
    """Implementation for writing walnut image embedding data using SQLAlchemy ORM."""

    def __init__(self, session: Session) -> None:
        """
        Initialize the writer with a SQLAlchemy session.

        Args:
            session: SQLAlchemy Session instance (injected via DI container)
        """
        self.session = session

    def save(self, embedding: WalnutImageEmbeddingDAO) -> WalnutImageEmbeddingDAO:
        """Save an embedding to the database. Returns embedding with generated ID."""
        if embedding.embedding is None:
            raise ValueError("Embedding cannot be None")

        try:
            # Convert numpy array to list for pgvector
            if isinstance(embedding.embedding, np.ndarray):
                embedding.embedding = embedding.embedding.tolist()
            
            # Add to session and flush to get generated ID
            self.session.add(embedding)
            self.session.flush()  # Flush to get the generated ID without committing
            return embedding
        except Exception:
            self.session.rollback()
            raise

    def save_or_update(self, embedding: WalnutImageEmbeddingDAO) -> WalnutImageEmbeddingDAO:
        """Save or update an embedding. Returns embedding with ID."""
        try:
            if embedding.id is not None:
                # Update existing - fetch from database
                existing = self.session.get(WalnutImageEmbeddingDAO, embedding.id)
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
                
                self.session.flush()
                return existing
            else:
                # Insert new
                return self.save(embedding)
        except Exception:
            self.session.rollback()
            raise
