# application_layer/queries/walnut_comparison__query.py
"""Query service for walnut comparisons."""
from abc import ABC, abstractmethod
from typing import List, Optional

from application_layer.dtos.walnut_comparison__dto import WalnutComparisonDTO
from application_layer.mappers.walnut_comparison__mapper import IWalnutComparisonMapper
from infrastructure_layer.db_readers import IWalnutComparisonDBReader


class IWalnutComparisonQuery(ABC):
    """Interface for querying walnut comparisons."""

    @abstractmethod
    async def get_all_pairings_async(self) -> List[WalnutComparisonDTO]:
        """Get all walnut pairing results."""
        pass

    @abstractmethod
    async def get_pairings_by_walnut_id_async(self, walnut_id: str) -> List[WalnutComparisonDTO]:
        """Get all pairings for a specific walnut."""
        pass

    @abstractmethod
    async def get_pairing_async(self, walnut_id: str, compared_walnut_id: str) -> Optional[WalnutComparisonDTO]:
        """Get a specific pairing between two walnuts."""
        pass


class WalnutComparisonQuery(IWalnutComparisonQuery):
    """Implementation of IWalnutComparisonQuery."""

    def __init__(
        self,
        comparison_reader: IWalnutComparisonDBReader,
        comparison_mapper: IWalnutComparisonMapper,
    ) -> None:
        """
        Initialize the query service.

        Args:
            comparison_reader: IWalnutComparisonDBReader instance
            comparison_mapper: IWalnutComparisonMapper instance
        """
        self.comparison_reader: IWalnutComparisonDBReader = comparison_reader
        self.comparison_mapper: IWalnutComparisonMapper = comparison_mapper

    async def get_all_pairings_async(self) -> List[WalnutComparisonDTO]:
        """Get all walnut pairing results."""
        daos = await self.comparison_reader.get_all_async()
        return self.comparison_mapper.daos_to_dtos(daos)

    async def get_pairings_by_walnut_id_async(self, walnut_id: str) -> List[WalnutComparisonDTO]:
        """Get all pairings for a specific walnut."""
        daos = await self.comparison_reader.get_by_walnut_id_async(walnut_id)
        return self.comparison_mapper.daos_to_dtos(daos)

    async def get_pairing_async(self, walnut_id: str, compared_walnut_id: str) -> Optional[WalnutComparisonDTO]:
        """Get a specific pairing between two walnuts."""
        dao = await self.comparison_reader.get_by_ids_async(walnut_id, compared_walnut_id)
        if dao is None:
            return None
        return self.comparison_mapper.dao_to_dto(dao)

