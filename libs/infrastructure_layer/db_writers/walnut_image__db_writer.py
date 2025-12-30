# infrastructure_layer/db_writers/walnut_image__db_writer.py
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from common.constants import DEFAULT_EMBEDDING_MODEL
from infrastructure_layer.data_access_objects import WalnutImageDBDAO
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from .walnut_image_embedding__db_writer import IWalnutImageEmbeddingDBWriter


class IWalnutImageDBWriter(ABC):
    """Interface for writing walnut image data to the database."""

    @abstractmethod
    def save(self, image: WalnutImageDBDAO) -> WalnutImageDBDAO:
        """Save an image to the database. Returns image with generated ID."""
        pass

    @abstractmethod
    def save_or_update(self, image: WalnutImageDBDAO) -> WalnutImageDBDAO:
        """Save or update an image. Returns image with ID."""
        pass

    @abstractmethod
    def save_with_embedding(self, image: WalnutImageDBDAO, model_name: str = DEFAULT_EMBEDDING_MODEL) -> WalnutImageDBDAO:
        """Save an image with its embedding. Returns image with IDs."""
        pass


class WalnutImageDBWriter(IWalnutImageDBWriter):
    """Implementation for writing walnut image data using SQLAlchemy ORM."""

    def __init__(
        self,
        session: Session,
        embedding_writer: "IWalnutImageEmbeddingDBWriter",
    ) -> None:
        """
        Initialize the writer with a SQLAlchemy session and embedding writer.

        Args:
            session: SQLAlchemy Session instance (injected via DI container)
            embedding_writer: IWalnutImageEmbeddingDBWriter instance (injected via DI container)
        """
        self.session: Session = session
        self.embedding_writer: "IWalnutImageEmbeddingDBWriter" = embedding_writer

    def save(self, image: WalnutImageDBDAO) -> WalnutImageDBDAO:
        """Save an image to the database. Returns image with generated ID."""
        try:
            # For new objects (without id or id is 0), use add() instead of merge()
            # This avoids SQLAlchemy's sentinel column detection
            image_id = getattr(image, "id", None)
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

    def save_or_update(self, image: WalnutImageDBDAO) -> WalnutImageDBDAO:
        """Save or update an image. Returns image with ID."""
        if image.id is not None:
            # Update existing - fetch from database
            existing = self.session.get(WalnutImageDBDAO, image.id)
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

    def save_with_embedding(self, image: WalnutImageDBDAO, model_name: str = DEFAULT_EMBEDDING_MODEL) -> WalnutImageDBDAO:
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
