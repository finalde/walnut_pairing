# infrastructure_layer/db_readers/walnut_image__db_reader.py
"""Database reader for walnut images."""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

from common.interfaces import IDatabaseConnection

from ..data_access_objects import WalnutImageDBDAO

if TYPE_CHECKING:
    from .walnut_image_embedding__db_reader import IWalnutImageEmbeddingDBReader


class IWalnutImageDBReader(ABC):
    """Interface for reading walnut image data from database."""

    @abstractmethod
    def get_by_id(self, image_id: int) -> Optional[WalnutImageDBDAO]:
        """Get a walnut image by its ID without embedding."""
        pass

    @abstractmethod
    def get_by_walnut_id(self, walnut_id: str) -> List[WalnutImageDBDAO]:
        """Get all images for a specific walnut without embeddings."""
        pass

    @abstractmethod
    def get_by_walnut_id_with_embeddings(self, walnut_id: str) -> List[WalnutImageDBDAO]:
        """Get all images for a specific walnut with their embeddings loaded."""
        pass

    @abstractmethod
    def get_by_id_with_embedding(self, image_id: int) -> Optional[WalnutImageDBDAO]:
        """Get a walnut image by ID with its embedding loaded."""
        pass


class WalnutImageDBReader(IWalnutImageDBReader):
    """Implementation of IWalnutImageDBReader for reading walnut image data from PostgreSQL."""

    def __init__(
        self,
        db_connection: IDatabaseConnection,
        embedding_reader: "IWalnutImageEmbeddingDBReader",
    ) -> None:
        """
        Initialize the reader with a database connection and embedding reader.

        Args:
            db_connection: IDatabaseConnection instance (injected via DI container)
            embedding_reader: IWalnutImageEmbeddingDBReader instance (injected via DI container).
        """
        self.db_connection: IDatabaseConnection = db_connection
        self.embedding_reader: "IWalnutImageEmbeddingDBReader" = embedding_reader

    def get_by_id(self, image_id: int) -> Optional[WalnutImageDBDAO]:
        """Get a walnut image by its ID without embedding."""
        with self.db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, walnut_id, side, image_path, width, height, checksum,
                       created_at, created_by, updated_at, updated_by
                FROM walnut_image
                WHERE id = %s
                """,
                (image_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None

            return WalnutImageDBDAO(
                id=row[0],
                walnut_id=row[1],
                side=row[2],
                image_path=row[3],
                width=row[4],
                height=row[5],
                checksum=row[6],
                created_at=row[7],
                created_by=row[8],
                updated_at=row[9],
                updated_by=row[10],
            )

    def get_by_walnut_id(self, walnut_id: str) -> List[WalnutImageDBDAO]:
        """Get all images for a specific walnut without embeddings."""
        with self.db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, walnut_id, side, image_path, width, height, checksum, walnut_width_px, walnut_height_px,
                       camera_distance_mm, focal_length_px,
                       created_at, created_by, updated_at, updated_by
                FROM walnut_image
                WHERE walnut_id = %s
                ORDER BY side
                """,
                (walnut_id,),
            )
            rows = cursor.fetchall()
            return [
                WalnutImageDBDAO(
                    id=row[0],
                    walnut_id=row[1],
                    side=row[2],
                    image_path=row[3],
                    width=row[4],
                    height=row[5],
                    checksum=row[6],
                    walnut_width_px=row[7],
                    walnut_height_px=row[8],
                    camera_distance_mm=row[9],
                    focal_length_px=row[10],
                    created_at=row[11],
                    created_by=row[12],
                    updated_at=row[13],
                    updated_by=row[14],
                )
                for row in rows
            ]

    def get_by_walnut_id_with_embeddings(self, walnut_id: str) -> List[WalnutImageDBDAO]:
        """Get all images for a specific walnut with their embeddings loaded."""
        images = self.get_by_walnut_id(walnut_id)

        # Load embeddings for each image
        for image in images:
            if image.id is not None:
                image.embedding = self.embedding_reader.get_by_image_id(image.id)

        return images

    def get_by_id_with_embedding(self, image_id: int) -> Optional[WalnutImageDBDAO]:
        """Get a walnut image by ID with its embedding loaded."""
        image = self.get_by_id(image_id)
        if image is None:
            return None

        # Load embedding
        if image.id is not None:
            image.embedding = self.embedding_reader.get_by_image_id(image.id)

        return image
