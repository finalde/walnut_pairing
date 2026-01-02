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
    - Similarity score must be between 0 and 1 (0 = identical, 1 = completely different)
    """

    walnut_id: str
    compared_walnut_id: str
    width_diff_mm: float
    height_diff_mm: float
    thickness_diff_mm: float
    similarity_score: float
    width_weight: float
    height_weight: float
    thickness_weight: float

    @classmethod
    def create(
        cls,
        walnut_id: str,
        compared_walnut_id: str,
        width_diff_mm: float,
        height_diff_mm: float,
        thickness_diff_mm: float,
        similarity_score: float,
        width_weight: float,
        height_weight: float,
        thickness_weight: float,
    ) -> Either["WalnutComparisonValueObject", DomainError]:
        """
        Create walnut comparison value object with validation.
        
        Business rules:
        - Both walnut IDs must be non-empty
        - Both walnut IDs must be different
        - Similarity score must be between 0 and 1
        - Weights must be between 0 and 1
        - Weights should sum to approximately 1.0 (with small tolerance)
        """
        # Check both IDs are non-empty
        if not walnut_id or not compared_walnut_id:
            return Left(ValidationError("Both walnut IDs must be non-empty"))

        # Check IDs are different
        if walnut_id == compared_walnut_id:
            return Left(ValidationError("Cannot compare a walnut with itself"))

        # Check similarity score is in valid range (0-1)
        if not (0.0 <= similarity_score <= 1.0):
            return Left(ValidationError(f"Similarity score must be between 0 and 1, got {similarity_score}"))

        # Check weights are in valid range (0-1)
        if not (0.0 <= width_weight <= 1.0):
            return Left(ValidationError(f"Width weight must be between 0 and 1, got {width_weight}"))
        if not (0.0 <= height_weight <= 1.0):
            return Left(ValidationError(f"Height weight must be between 0 and 1, got {height_weight}"))
        if not (0.0 <= thickness_weight <= 1.0):
            return Left(ValidationError(f"Thickness weight must be between 0 and 1, got {thickness_weight}"))

        # Check weights sum to approximately 1.0 (with tolerance of 0.01)
        weight_sum = width_weight + height_weight + thickness_weight
        if abs(weight_sum - 1.0) > 0.01:
            return Left(ValidationError(f"Weights must sum to 1.0, got {weight_sum}"))

        return Right(
            cls(
                walnut_id=walnut_id,
                compared_walnut_id=compared_walnut_id,
                width_diff_mm=width_diff_mm,
                height_diff_mm=height_diff_mm,
                thickness_diff_mm=thickness_diff_mm,
                similarity_score=similarity_score,
                width_weight=width_weight,
                height_weight=height_weight,
                thickness_weight=thickness_weight,
            )
        )

