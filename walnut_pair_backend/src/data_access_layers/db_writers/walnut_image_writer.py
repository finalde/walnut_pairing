# src/data_access_layers/db_writers/walnut_image_writer.py
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from typing import TYPE_CHECKING
from src.data_access_layers.data_access_objects import WalnutImageDAO

if TYPE_CHECKING:
    from .walnut_image_embedding_writer import IWalnutImageEmbeddingWriter


class IWalnutImageWriter(ABC):
    """Interface for writing walnut image data to the database."""

    @abstractmethod
    def save(self, image: WalnutImageDAO) -> WalnutImageDAO:
        """Save an image to the database. Returns image with generated ID."""
        pass

    @abstractmethod
    def save_or_update(self, image: WalnutImageDAO) -> WalnutImageDAO:
        """Save or update an image. Returns image with ID."""
        pass

    @abstractmethod
    def save_with_embedding(
        self, image: WalnutImageDAO, model_name: str = "resnet50-imagenet"
    ) -> WalnutImageDAO:
        """Save an image with its embedding. Returns image with IDs."""
        pass


class WalnutImageWriter(IWalnutImageWriter):
    """Implementation for writing walnut image data using SQLAlchemy ORM."""

    def __init__(
        self,
        session: Session,
        embedding_writer: "IWalnutImageEmbeddingWriter",
    ) -> None:
        """
        Initialize the writer with a SQLAlchemy session and embedding writer.

        Args:
            session: SQLAlchemy Session instance (injected via DI container)
            embedding_writer: IWalnutImageEmbeddingWriter instance (injected via DI container)
        """
        self.session = session
        self.embedding_writer = embedding_writer

    def save(self, image: WalnutImageDAO) -> WalnutImageDAO:
        """Save an image to the database. Returns image with generated ID."""
        try:
            # For new objects (without id or id is 0), use add() instead of merge()
            # This avoids SQLAlchemy's sentinel column detection
            image_id = getattr(image, 'id', None)
            if image_id is None or image_id == 0:
                # New object - use add()
                self.session.add(image)
            else:
                # Existing object - use merge()
                image = self.session.merge(image)
            self.session.flush()  # Flush to get the generated ID without committing
            return image
        except Exception:
            self.session.rollback()
            raise

    def save_or_update(self, image: WalnutImageDAO) -> WalnutImageDAO:
        """Save or update an image. Returns image with ID."""
        if image.id is not None:
            # Update existing - fetch from database
            existing = self.session.get(WalnutImageDAO, image.id)
            if existing is None:
                raise ValueError(f"Image with id {image.id} not found")
            
            # Update fields
            existing.image_path = image.image_path
            existing.width = image.width
            existing.height = image.height
            existing.checksum = image.checksum
            existing.updated_by = image.updated_by
            # updated_at is set by database default
            
            self.session.flush()
            return existing
        else:
            # Insert new
            return self.save(image)

    def save_with_embedding(
        self, image: WalnutImageDAO, model_name: str = "resnet50-imagenet"
    ) -> WalnutImageDAO:
        """Save an image with its embedding. Returns image with IDs."""
        try:
            # Save image first
            image = self.save(image)

            # Save embedding if present
            if image.embedding is not None and image.id is not None:
                embedding = image.embedding
                embedding.image_id = image.id
                embedding.model_name = model_name
                saved_embedding = self.embedding_writer.save(embedding)
                image.embedding = saved_embedding
            
            self.session.commit()  # Commit the transaction
            return image
        except Exception:
            self.session.rollback()
            raise
