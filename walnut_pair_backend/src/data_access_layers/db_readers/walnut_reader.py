# src/data_access_layers/db_readers/walnut_reader.py
from abc import ABC, abstractmethod
from typing import Optional, List
from src.data_access_layers.data_access_objects.walnut_dao import WalnutDAO


class IWalnutReader(ABC):
    """Interface for reading walnut data from the database."""

    @abstractmethod
    def get_by_id(self, walnut_id: str) -> Optional[WalnutDAO]:
        """Get a walnut by its ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[WalnutDAO]:
        """Get all walnuts from the database."""
        pass

    @abstractmethod
    def get_by_id_with_images(
        self, walnut_id: str
    ) -> Optional[WalnutDAO]:
        """Get a walnut by ID with its related images loaded."""
        pass


class WalnutReader(IWalnutReader):
    """Implementation of IWalnutReader for reading walnut data from PostgreSQL."""

    def __init__(self, db_connection) -> None:
        """
        Initialize the reader with a database connection.

        Args:
            db_connection: A database connection object (e.g., psycopg2 connection)
        """
        self.db_connection = db_connection

    def get_by_id(self, walnut_id: str) -> Optional[WalnutDAO]:
        """Get a walnut by its ID without related images."""
        with self.db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, description, created_at, created_by, updated_at, updated_by
                FROM walnut
                WHERE id = %s
                """,
                (walnut_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None

            return WalnutDAO(
                id=row[0],
                description=row[1],
                created_at=row[2],
                created_by=row[3],
                updated_at=row[4],
                updated_by=row[5],
            )

    def get_all(self) -> List[WalnutDAO]:
        """Get all walnuts from the database."""
        with self.db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, description, created_at, created_by, updated_at, updated_by
                FROM walnut
                ORDER BY created_at DESC
                """
            )
            rows = cursor.fetchall()
            return [
                WalnutDAO(
                    id=row[0],
                    description=row[1],
                    created_at=row[2],
                    created_by=row[3],
                    updated_at=row[4],
                    updated_by=row[5],
                )
                for row in rows
            ]

    def get_by_id_with_images(
        self, walnut_id: str
    ) -> Optional[WalnutDAO]:
        """Get a walnut by ID with its related images loaded."""
        from src.data_access_layers.db_readers.walnut_image_reader import (
            WalnutImageReader,
        )

        walnut = self.get_by_id(walnut_id)
        if walnut is None:
            return None

        # Load related images
        image_reader = WalnutImageReader(self.db_connection)
        walnut.images = image_reader.get_by_walnut_id_with_embeddings(
            walnut_id
        )

        return walnut

