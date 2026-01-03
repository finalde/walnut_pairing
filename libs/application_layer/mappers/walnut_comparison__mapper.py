# application_layer/mappers/walnut_comparison__mapper.py
from abc import ABC, abstractmethod
from typing import List

from common.constants import SYSTEM_USER
from domain_layer.value_objects.walnut_comparison__value_object import WalnutComparisonValueObject
from infrastructure_layer.data_access_objects.walnut_comparison__db_dao import WalnutComparisonDBDAO
from application_layer.dtos.walnut_comparison__dto import WalnutComparisonDTO


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

    @abstractmethod
    def dao_to_dto(self, comparison_dao: WalnutComparisonDBDAO) -> WalnutComparisonDTO:
        """Convert WalnutComparisonDBDAO to WalnutComparisonDTO."""
        pass

    @abstractmethod
    def daos_to_dtos(self, comparison_daos: List[WalnutComparisonDBDAO]) -> List[WalnutComparisonDTO]:
        """Convert a list of WalnutComparisonDBDAO to a list of WalnutComparisonDTO."""
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
            basic_similarity=comparison_vo.basic_similarity,
            width_weight=comparison_vo.width_weight,
            height_weight=comparison_vo.height_weight,
            thickness_weight=comparison_vo.thickness_weight,
            front_embedding_score=comparison_vo.front_embedding_score,
            back_embedding_score=comparison_vo.back_embedding_score,
            left_embedding_score=comparison_vo.left_embedding_score,
            right_embedding_score=comparison_vo.right_embedding_score,
            top_embedding_score=comparison_vo.top_embedding_score,
            down_embedding_score=comparison_vo.down_embedding_score,
            advanced_similarity=comparison_vo.advanced_similarity,
            final_similarity=comparison_vo.final_similarity,
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

    def dao_to_dto(self, comparison_dao: WalnutComparisonDBDAO) -> WalnutComparisonDTO:
        """Convert WalnutComparisonDBDAO to WalnutComparisonDTO."""
        return WalnutComparisonDTO(
            id=comparison_dao.id,
            walnut_id=comparison_dao.walnut_id,
            compared_walnut_id=comparison_dao.compared_walnut_id,
            width_diff_mm=comparison_dao.width_diff_mm,
            height_diff_mm=comparison_dao.height_diff_mm,
            thickness_diff_mm=comparison_dao.thickness_diff_mm,
            basic_similarity=comparison_dao.basic_similarity,
            advanced_similarity=comparison_dao.advanced_similarity,
            final_similarity=comparison_dao.final_similarity,
            created_at=comparison_dao.created_at,
            updated_at=comparison_dao.updated_at,
        )

    def daos_to_dtos(self, comparison_daos: List[WalnutComparisonDBDAO]) -> List[WalnutComparisonDTO]:
        """Convert a list of WalnutComparisonDBDAO to a list of WalnutComparisonDTO."""
        return [self.dao_to_dto(dao) for dao in comparison_daos]
