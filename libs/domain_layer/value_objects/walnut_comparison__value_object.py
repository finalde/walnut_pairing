# domain_layer/value_objects/walnut_comparison__value_object.py
from dataclasses import dataclass
from typing import Optional

from common.either import Either, Left, Right
from common.enums import WalnutSideEnum
from domain_layer.domain_error import DomainError, ValidationError


@dataclass(frozen=True)
class WalnutComparisonValueObject:
    """
    Value object representing a comparison between two walnuts.
    
    Business invariants:
    - Both walnut IDs must be non-empty
    - Both walnut IDs must be different (cannot compare a walnut with itself)
    - All similarity scores must be between 0 and 1
    - Final similarity must be present if either basic or advanced is present
    """

    walnut_id: str
    compared_walnut_id: str
    # Basic similarity metrics
    width_diff_mm: float
    height_diff_mm: float
    thickness_diff_mm: float
    basic_similarity: Optional[float]
    width_weight: float
    height_weight: float
    thickness_weight: float
    # Advanced similarity metrics (embedding scores)
    front_embedding_score: Optional[float]
    back_embedding_score: Optional[float]
    left_embedding_score: Optional[float]
    right_embedding_score: Optional[float]
    top_embedding_score: Optional[float]
    down_embedding_score: Optional[float]
    advanced_similarity: Optional[float]
    # Final combined similarity
    final_similarity: float

    @classmethod
    def create(
        cls,
        walnut_id: str,
        compared_walnut_id: str,
        width_diff_mm: float,
        height_diff_mm: float,
        thickness_diff_mm: float,
        basic_similarity: Optional[float],
        width_weight: float,
        height_weight: float,
        thickness_weight: float,
        front_embedding_score: Optional[float],
        back_embedding_score: Optional[float],
        left_embedding_score: Optional[float],
        right_embedding_score: Optional[float],
        top_embedding_score: Optional[float],
        down_embedding_score: Optional[float],
        advanced_similarity: Optional[float],
        final_similarity: float,
    ) -> Either["WalnutComparisonValueObject", DomainError]:
        """
        Create walnut comparison value object with validation.
        
        Business rules:
        - Both walnut IDs must be non-empty
        - Both walnut IDs must be different
        - All similarity scores (if present) must be between 0 and 1
        - At least one of basic_similarity or advanced_similarity must be present
        - Final similarity must be between 0 and 1
        - Weights must be between 0 and 1
        - Basic weights should sum to approximately 1.0
        """
        # Check both IDs are non-empty
        if not walnut_id or not compared_walnut_id:
            return Left(ValidationError("Both walnut IDs must be non-empty"))

        # Check IDs are different
        if walnut_id == compared_walnut_id:
            return Left(ValidationError("Cannot compare a walnut with itself"))

        # Check at least one similarity is present
        if basic_similarity is None and advanced_similarity is None:
            return Left(ValidationError("At least one of basic_similarity or advanced_similarity must be present"))

        # Check basic similarity is in valid range (if present)
        if basic_similarity is not None and not (0.0 <= basic_similarity <= 1.0):
            return Left(ValidationError(f"Basic similarity must be between 0 and 1, got {basic_similarity}"))

        # Check advanced similarity is in valid range (if present)
        if advanced_similarity is not None and not (0.0 <= advanced_similarity <= 1.0):
            return Left(ValidationError(f"Advanced similarity must be between 0 and 1, got {advanced_similarity}"))

        # Check side embedding scores are in valid range (if present)
        side_embedding_scores = {
            "front": front_embedding_score,
            "back": back_embedding_score,
            "left": left_embedding_score,
            "right": right_embedding_score,
            "top": top_embedding_score,
            "down": down_embedding_score,
        }
        for side_name, score in side_embedding_scores.items():
            if score is not None and not (0.0 <= score <= 1.0):
                return Left(ValidationError(f"{side_name} embedding score must be between 0 and 1, got {score}"))

        # Check final similarity is in valid range
        if not (0.0 <= final_similarity <= 1.0):
            return Left(ValidationError(f"Final similarity must be between 0 and 1, got {final_similarity}"))

        # Check weights are in valid range (0-1)
        if not (0.0 <= width_weight <= 1.0):
            return Left(ValidationError(f"Width weight must be between 0 and 1, got {width_weight}"))
        if not (0.0 <= height_weight <= 1.0):
            return Left(ValidationError(f"Height weight must be between 0 and 1, got {height_weight}"))
        if not (0.0 <= thickness_weight <= 1.0):
            return Left(ValidationError(f"Thickness weight must be between 0 and 1, got {thickness_weight}"))

        # Check basic weights sum to approximately 1.0 (with tolerance of 0.01)
        weight_sum = width_weight + height_weight + thickness_weight
        if abs(weight_sum - 1.0) > 0.01:
            return Left(ValidationError(f"Basic weights must sum to 1.0, got {weight_sum}"))

        return Right(
            cls(
                walnut_id=walnut_id,
                compared_walnut_id=compared_walnut_id,
                width_diff_mm=width_diff_mm,
                height_diff_mm=height_diff_mm,
                thickness_diff_mm=thickness_diff_mm,
                basic_similarity=basic_similarity,
                width_weight=width_weight,
                height_weight=height_weight,
                thickness_weight=thickness_weight,
                front_embedding_score=front_embedding_score,
                back_embedding_score=back_embedding_score,
                left_embedding_score=left_embedding_score,
                right_embedding_score=right_embedding_score,
                top_embedding_score=top_embedding_score,
                down_embedding_score=down_embedding_score,
                advanced_similarity=advanced_similarity,
                final_similarity=final_similarity,
            )
        )
