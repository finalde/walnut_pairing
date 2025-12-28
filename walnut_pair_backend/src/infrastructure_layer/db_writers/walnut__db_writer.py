# src/infrastructure_layer/db_writers/walnut__db_writer.py
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from typing import TYPE_CHECKING
from src.infrastructure_layer.data_access_objects import WalnutDBDAO

if TYPE_CHECKING:
    from .walnut_image__db_writer import IWalnutImageDBWriter


class IWalnutDBWriter(ABC):
    """Interface for writing walnut data to the database."""

    @abstractmethod
    def save(self, walnut: WalnutDBDAO) -> WalnutDBDAO:
        """Save a walnut to the database. Returns walnut with timestamps."""
        pass

    @abstractmethod
    def save_with_images(self, walnut: WalnutDBDAO) -> WalnutDBDAO:
        """Save a walnut with all its images and embeddings. Returns walnut with IDs."""
        pass

    @abstractmethod
    def save_or_update(self, walnut: WalnutDBDAO) -> WalnutDBDAO:
        """Save or update a walnut. Returns walnut with timestamps."""
        pass


class WalnutDBWriter(IWalnutDBWriter):
    """Implementation for writing walnut data using SQLAlchemy ORM."""

    def __init__(
        self,
        session: Session,
        image_writer: "IWalnutImageDBWriter",
    ) -> None:
        """
        Initialize the writer with a SQLAlchemy session and image writer.

        Args:
            session: SQLAlchemy Session instance (injected via DI container)
            image_writer: IWalnutImageDBWriter instance (injected via DI container)
        """
        self.session: Session = session
        self.image_writer: "IWalnutImageDBWriter" = image_writer

    def save(self, walnut: WalnutDBDAO) -> WalnutDBDAO:
        """Save a walnut to the database. Returns walnut with timestamps."""
        # Use merge for upsert (handles ON CONFLICT logic)
        walnut = self.session.merge(walnut)
        self.session.flush()  # Flush to get timestamps without committing
        return walnut

    def save_with_images(self, walnut: WalnutDBDAO) -> WalnutDBDAO:
        """
        Save a walnut with all its images and embeddings using SQLAlchemy ORM.
        This is the ORM-like save that cascades to images and embeddings.
        Returns walnut with all IDs populated.
        
        If the walnut already exists, it will be deleted first (along with its images and embeddings)
        due to CASCADE delete, then the new walnut will be inserted.
        """
        try:
            walnut_id = getattr(walnut, 'id', None)
            if walnut_id is None or walnut_id == "":
                # New object - use add() which will cascade to images and embeddings
                self.session.add(walnut)
            else:
                # Check if walnut exists - if so, delete it first (CASCADE will delete images/embeddings)
                existing = self.session.get(WalnutDBDAO, walnut_id)
                if existing is not None:
                    # Delete existing walnut (CASCADE will delete images and embeddings)
                    self.session.delete(existing)
                    self.session.flush()  # Flush the delete
                
                # Now add the new walnut with its images and embeddings
                self.session.add(walnut)
            
            self.session.flush()  # Flush to get all generated IDs without committing
            self.session.commit()  # Commit the transaction
            return walnut
        except Exception:
            self.session.rollback()
            raise

    def save_or_update(self, walnut: WalnutDBDAO) -> WalnutDBDAO:
        """Save or update a walnut. Returns walnut with timestamps."""
        # The save method already handles upsert with merge
        return self.save(walnut)
