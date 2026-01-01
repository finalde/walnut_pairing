# domain_layer/entities/walnut_comparison__entity.py
from typing import List

from common.either import Either, Left, Right
from domain_layer.domain_error import DomainError, ValidationError
from domain_layer.domain_services.walnut_comparison__domain_service import WalnutComparisonDomainService
from domain_layer.entities.walnut__entity import WalnutEntity
from domain_layer.value_objects.walnut_comparison__value_object import WalnutComparisonValueObject


class WalnutComparisonEntity:
    """
    Domain entity representing a walnut comparison operation.
    
    Business rules:
    - Contains a list of walnut entities to compare
    - For each main walnut, compares it with all other walnuts
    - Generates comparison value objects for each pair
    - Ensures all walnuts have valid dimensions before comparison
    """

    def __new__(cls, walnuts: List[WalnutEntity]) -> "WalnutComparisonEntity":
        raise RuntimeError("WalnutComparisonEntity cannot be instantiated directly. Use WalnutComparisonEntity.create() instead.")

    def __init__(self, walnuts: List[WalnutEntity]) -> None:
        self.walnuts: List[WalnutEntity] = walnuts
        self._initialized: bool = True

    @staticmethod
    def create(walnuts: List[WalnutEntity]) -> Either["WalnutComparisonEntity", DomainError]:
        """
        Create a WalnutComparisonEntity with validation.
        
        Business rules:
        - Must have at least 2 walnuts
        - All walnuts must have valid dimensions
        """
        if len(walnuts) < 2:
            return Left(ValidationError("Need at least 2 walnuts to perform comparison"))

        # Validate all walnuts have dimensions
        for walnut in walnuts:
            if walnut.dimensions is None:
                return Left(ValidationError(f"Walnut {walnut.id} does not have dimensions"))

        entity = object.__new__(WalnutComparisonEntity)
        entity.__init__(walnuts)
        return Right(entity)

    def compare_all(self) -> List[WalnutComparisonValueObject]:
        """
        Compare all walnuts and generate comparison value objects.
        
        Business rule: For each main walnut, compare it with all other walnuts.
        Only compares A-B, not B-A (no duplicates).
        
        Returns:
            List of WalnutComparisonValueObject for all pairs
        """
        comparisons: List[WalnutComparisonValueObject] = []

        # For each main walnut, compare with all others
        for i, main_walnut in enumerate(self.walnuts):
            for j, other_walnut in enumerate(self.walnuts):
                # Skip same walnut (A-A) and reverse pairs (B-A if we already did A-B)
                if i >= j:
                    continue

                # Calculate comparison using domain service
                comparison_vo = WalnutComparisonDomainService.calculate_comparison(
                    walnut1_id=main_walnut.id,
                    walnut1_dimensions=main_walnut.dimensions,
                    walnut2_id=other_walnut.id,
                    walnut2_dimensions=other_walnut.dimensions,
                )

                comparisons.append(comparison_vo)

        return comparisons

