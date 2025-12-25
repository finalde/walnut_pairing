# src/data_access_layers/db_readers/walnut_image_embedding_reader.py
from abc import ABC, abstractmethod
from typing import Optional, List
import numpy as np
from src.data_access_layers.data_access_objects.walnut_image_embedding_dao import (
    WalnutImageEmbeddingDAO,
)
from src.common.interfaces import IDatabaseConnection


class IWalnutImageEmbeddingReader(ABC):
    """Interface for reading walnut image embedding data from the database."""

    @abstractmethod
    def get_by_id(self, embedding_id: int) -> Optional[WalnutImageEmbeddingDAO]:
        """Get an embedding by its ID."""
        pass

    @abstractmethod
    def get_by_image_id(
        self, image_id: int
    ) -> Optional[WalnutImageEmbeddingDAO]:
        """Get an embedding by image ID (one-to-one relationship)."""
        pass

    @abstractmethod
    def get_by_model_name(
        self, model_name: str
    ) -> List[WalnutImageEmbeddingDAO]:
        """Get all embeddings for a specific model."""
        pass


class WalnutImageEmbeddingReader(IWalnutImageEmbeddingReader):
    """Implementation of IWalnutImageEmbeddingReader for reading embedding data from PostgreSQL."""

    def __init__(self, db_connection: IDatabaseConnection) -> None:
        """
        Initialize the reader with a database connection.

        Args:
            db_connection: IDatabaseConnection instance (injected via DI container)
        """
        self.db_connection = db_connection

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

    def get_by_id(
        self, embedding_id: int
    ) -> Optional[WalnutImageEmbeddingDAO]:
        """Get an embedding by its ID."""
        with self.db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, image_id, model_name, embedding, created_at, created_by,
                       updated_at, updated_by
                FROM walnut_image_embedding
                WHERE id = %s
                """,
                (embedding_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None

            embedding_vector = self._vector_to_numpy(row[3])

            return WalnutImageEmbeddingDAO(
                id=row[0],
                image_id=row[1],
                model_name=row[2],
                embedding=embedding_vector,
                created_at=row[4],
                created_by=row[5],
                updated_at=row[6],
                updated_by=row[7],
            )

    def get_by_image_id(
        self, image_id: int
    ) -> Optional[WalnutImageEmbeddingDAO]:
        """Get an embedding by image ID (one-to-one relationship)."""
        with self.db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, image_id, model_name, embedding, created_at, created_by,
                       updated_at, updated_by
                FROM walnut_image_embedding
                WHERE image_id = %s
                LIMIT 1
                """,
                (image_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None

            embedding_vector = self._vector_to_numpy(row[3])

            return WalnutImageEmbeddingDAO(
                id=row[0],
                image_id=row[1],
                model_name=row[2],
                embedding=embedding_vector,
                created_at=row[4],
                created_by=row[5],
                updated_at=row[6],
                updated_by=row[7],
            )

    def get_by_model_name(
        self, model_name: str
    ) -> List[WalnutImageEmbeddingDAO]:
        """Get all embeddings for a specific model."""
        with self.db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, image_id, model_name, embedding, created_at, created_by,
                       updated_at, updated_by
                FROM walnut_image_embedding
                WHERE model_name = %s
                ORDER BY created_at DESC
                """,
                (model_name,),
            )
            rows = cursor.fetchall()
            return [
                WalnutImageEmbeddingDAO(
                    id=row[0],
                    image_id=row[1],
                    model_name=row[2],
                    embedding=self._vector_to_numpy(row[3]),
                    created_at=row[4],
                    created_by=row[5],
                    updated_at=row[6],
                    updated_by=row[7],
                )
                for row in rows
            ]

