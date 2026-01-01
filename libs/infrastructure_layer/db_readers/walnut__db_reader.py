# infrastructure_layer/db_readers/walnut__reader.py
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

from common.interfaces import IDatabaseConnection

from ..data_access_objects import WalnutDBDAO

if TYPE_CHECKING:
    from .walnut_image__db_reader import IWalnutImageDBReader


class IWalnutDBReader(ABC):
    """Interface for reading walnut data from the database."""

    @abstractmethod
    def get_by_id(self, walnut_id: str) -> Optional[WalnutDBDAO]:
        """Get a walnut by its ID with related images and embeddings loaded."""
        pass

    @abstractmethod
    def get_all(self) -> List[WalnutDBDAO]:
        """Get all walnuts from the database with related images and embeddings loaded."""
        pass

    @abstractmethod
    def get_by_id_with_images(self, walnut_id: str) -> Optional[WalnutDBDAO]:
        """Get a walnut by ID with its related images and embeddings loaded.

        Note: This method now delegates to get_by_id() which already loads
        images and embeddings. Kept for backward compatibility.
        """
        pass


class WalnutDBReader(IWalnutDBReader):
    """Implementation of IWalnutDBReader for reading walnut data from PostgreSQL."""

    def __init__(
        self,
        db_connection: IDatabaseConnection,
        image_reader: "IWalnutImageDBReader",
    ) -> None:
        """
        Initialize the reader with a database connection and image reader.

        Args:
            db_connection: IDatabaseConnection instance (injected via DI container)
            image_reader: IWalnutImageDBReader instance (injected via DI container).
        """
        self.db_connection: IDatabaseConnection = db_connection
        self.image_reader: "IWalnutImageDBReader" = image_reader

    def get_by_id(self, walnut_id: str) -> Optional[WalnutDBDAO]:
        """Get a walnut by its ID with related images and embeddings loaded."""
        with self.db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, description, width_mm, height_mm, thickness_mm, created_at, created_by, updated_at, updated_by
                FROM walnut
                WHERE id = %s
                """,
                (walnut_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None

            walnut = WalnutDBDAO(
                id=row[0],
                description=row[1],
                width_mm=row[2],
                height_mm=row[3],
                thickness_mm=row[4],
                created_at=row[5],
                created_by=row[6],
                updated_at=row[7],
                updated_by=row[8],
            )

            # Load related images with embeddings
            walnut.images = self.image_reader.get_by_walnut_id_with_embeddings(walnut_id)

            return walnut

    def get_all(self) -> List[WalnutDBDAO]:
        """Get all walnuts from the database with related images and embeddings loaded."""
        with self.db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, description, width_mm, height_mm, thickness_mm, created_at, created_by, updated_at, updated_by
                FROM walnut
                ORDER BY created_at DESC
                """
            )
            rows = cursor.fetchall()
            walnuts = [
                WalnutDBDAO(
                    id=row[0],
                    description=row[1],
                    width_mm=row[2],
                    height_mm=row[3],
                    thickness_mm=row[4],
                    created_at=row[5],
                    created_by=row[6],
                    updated_at=row[7],
                    updated_by=row[8],
                )
                for row in rows
            ]

            # Load related images with embeddings for each walnut
            for walnut in walnuts:
                walnut.images = self.image_reader.get_by_walnut_id_with_embeddings(walnut.id)

            return walnuts

    def get_by_id_with_images(self, walnut_id: str) -> Optional[WalnutDBDAO]:
        """Get a walnut by ID with its related images and embeddings loaded.

        Note: This method now delegates to get_by_id() which already loads
        images and embeddings. Kept for backward compatibility.
        """
        return self.get_by_id(walnut_id)
