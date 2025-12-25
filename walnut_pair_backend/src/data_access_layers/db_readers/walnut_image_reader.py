# src/data_access_layers/db_readers/walnut_image_reader.py
from abc import ABC, abstractmethod
from typing import Optional, List
from ..data_access_objects import (
    WalnutImageDAO,
)


class IWalnutImageReader(ABC):
    """Interface for reading walnut image data from the database."""

    @abstractmethod
    def get_by_id(self, image_id: int) -> Optional[WalnutImageDAO]:
        """Get a walnut image by its ID."""
        pass

    @abstractmethod
    def get_by_walnut_id(self, walnut_id: str) -> List[WalnutImageDAO]:
        """Get all images for a specific walnut."""
        pass

    @abstractmethod
    def get_by_walnut_id_with_embeddings(
        self, walnut_id: str
    ) -> List[WalnutImageDAO]:
        """Get all images for a specific walnut with their embeddings loaded."""
        pass

    @abstractmethod
    def get_by_id_with_embedding(
        self, image_id: int
    ) -> Optional[WalnutImageDAO]:
        """Get a walnut image by ID with its embedding loaded."""
        pass


class WalnutImageReader(IWalnutImageReader):
    """Implementation of IWalnutImageReader for reading walnut image data from PostgreSQL."""

    def __init__(self, db_connection) -> None:
        """
        Initialize the reader with a database connection.

        Args:
            db_connection: A database connection object (e.g., psycopg2 connection)
        """
        self.db_connection = db_connection

    def get_by_id(self, image_id: int) -> Optional[WalnutImageDAO]:
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

            return WalnutImageDAO(
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

    def get_by_walnut_id(self, walnut_id: str) -> List[WalnutImageDAO]:
        """Get all images for a specific walnut without embeddings."""
        with self.db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, walnut_id, side, image_path, width, height, checksum,
                       created_at, created_by, updated_at, updated_by
                FROM walnut_image
                WHERE walnut_id = %s
                ORDER BY side
                """,
                (walnut_id,),
            )
            rows = cursor.fetchall()
            return [
                WalnutImageDAO(
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
                for row in rows
            ]

    def get_by_walnut_id_with_embeddings(
        self, walnut_id: str
    ) -> List[WalnutImageDAO]:
        """Get all images for a specific walnut with their embeddings loaded."""
        from .walnut_image_embedding_reader import (
            WalnutImageEmbeddingReader,
        )

        images = self.get_by_walnut_id(walnut_id)
        embedding_reader = WalnutImageEmbeddingReader(self.db_connection)

        # Load embeddings for each image
        for image in images:
            if image.id is not None:
                image.embedding = embedding_reader.get_by_image_id(image.id)

        return images

    def get_by_id_with_embedding(
        self, image_id: int
    ) -> Optional[WalnutImageDAO]:
        """Get a walnut image by ID with its embedding loaded."""
        from .walnut_image_embedding_reader import (
            WalnutImageEmbeddingReader,
        )

        image = self.get_by_id(image_id)
        if image is None:
            return None

        # Load embedding
        embedding_reader = WalnutImageEmbeddingReader(self.db_connection)
        if image.id is not None:
            image.embedding = embedding_reader.get_by_image_id(image.id)

        return image

