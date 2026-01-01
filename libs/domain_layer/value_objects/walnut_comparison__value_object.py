# domain_layer/value_objects/walnut_comparison__value_object.py
from dataclasses import dataclass

from common.either import Either, Left, Right
from domain_layer.domain_error import DomainError, ValidationError


@dataclass(frozen=True)
class WalnutComparisonValueObject:
    """
    Value object representing a comparison between two walnuts.
    
    Business invariants:
    - Both walnut IDs must be non-empty
    - Both walnut IDs must be different (cannot compare a walnut with itself)
    - All dimension differences must be non-negative (absolute differences)
    - Similarity score must be between 0 and 1 (0 = identical, 1 = completely different)
    """

    walnut_id: str
    compared_walnut_id: str
    width_diff_mm: float
    height_diff_mm: float
    thickness_diff_mm: float
    similarity_score: float

    @classmethod
    def create(
        cls,
        walnut_id: str,
        compared_walnut_id: str,
        width_diff_mm: float,
        height_diff_mm: float,
        thickness_diff_mm: float,
        similarity_score: float,
    ) -> Either["WalnutComparisonValueObject", DomainError]:
        """
        Create walnut comparison value object with validation.
        
        Business rules:
        - Both walnut IDs must be non-empty
        - Both walnut IDs must be different
        - All dimension differences must be non-negative
        - Similarity score must be between 0 and 1
        """
        # Check both IDs are non-empty
        if not walnut_id or not compared_walnut_id:
            return Left(ValidationError("Both walnut IDs must be non-empty"))

        # Check IDs are different
        if walnut_id == compared_walnut_id:
            return Left(ValidationError("Cannot compare a walnut with itself"))

        # Check dimension differences are non-negative (absolute differences)
        if width_diff_mm < 0 or height_diff_mm < 0 or thickness_diff_mm < 0:
            return Left(ValidationError("Dimension differences must be non-negative"))

        # Check similarity score is in valid range (0-1)
        if not (0.0 <= similarity_score <= 1.0):
            return Left(ValidationError(f"Similarity score must be between 0 and 1, got {similarity_score}"))

        return Right(
            cls(
                walnut_id=walnut_id,
                compared_walnut_id=compared_walnut_id,
                width_diff_mm=width_diff_mm,
                height_diff_mm=height_diff_mm,
                thickness_diff_mm=thickness_diff_mm,
                similarity_score=similarity_score,
            )
        )

