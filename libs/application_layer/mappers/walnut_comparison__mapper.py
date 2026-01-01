# application_layer/mappers/walnut_comparison__mapper.py
from abc import ABC, abstractmethod
from typing import List

from common.constants import SYSTEM_USER
from domain_layer.value_objects.walnut_comparison__value_object import WalnutComparisonValueObject
from infrastructure_layer.data_access_objects.walnut_comparison__db_dao import WalnutComparisonDBDAO


class IWalnutComparisonMapper(ABC):
    """Interface for mapping walnut comparison between domain and infrastructure layers."""

    @abstractmethod
    def value_object_to_dao(
        self,
        comparison_vo: WalnutComparisonValueObject,
        created_by: str,
        updated_by: str,
    ) -> WalnutComparisonDBDAO:
        """Convert WalnutComparisonValueObject to WalnutComparisonDBDAO."""
        pass

    @abstractmethod
    def value_objects_to_daos(
        self,
        comparison_vos: List[WalnutComparisonValueObject],
        created_by: str,
        updated_by: str,
    ) -> List[WalnutComparisonDBDAO]:
        """Convert a list of WalnutComparisonValueObject to a list of WalnutComparisonDBDAO."""
        pass


class WalnutComparisonMapper(IWalnutComparisonMapper):
    """Mapper for walnut comparison between domain and infrastructure layers."""

    def value_object_to_dao(
        self,
        comparison_vo: WalnutComparisonValueObject,
        created_by: str = SYSTEM_USER,
        updated_by: str = SYSTEM_USER,
    ) -> WalnutComparisonDBDAO:
        """Convert WalnutComparisonValueObject to WalnutComparisonDBDAO."""
        return WalnutComparisonDBDAO(
            walnut_id=comparison_vo.walnut_id,
            compared_walnut_id=comparison_vo.compared_walnut_id,
            width_diff_mm=comparison_vo.width_diff_mm,
            height_diff_mm=comparison_vo.height_diff_mm,
            thickness_diff_mm=comparison_vo.thickness_diff_mm,
            similarity_score=comparison_vo.similarity_score,
            created_by=created_by,
            updated_by=updated_by,
        )

    def value_objects_to_daos(
        self,
        comparison_vos: List[WalnutComparisonValueObject],
        created_by: str = SYSTEM_USER,
        updated_by: str = SYSTEM_USER,
    ) -> List[WalnutComparisonDBDAO]:
        """Convert a list of WalnutComparisonValueObject to a list of WalnutComparisonDBDAO."""
        return [
            self.value_object_to_dao(comparison_vo, created_by, updated_by)
            for comparison_vo in comparison_vos
        ]

