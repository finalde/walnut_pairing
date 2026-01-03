# domain_layer/entities/walnut_comparison__entity.py
from typing import Dict, List, Optional

from common.enums import ComparisonModeEnum, WalnutSideEnum
from common.either import Either, Left, Right
from domain_layer.domain_error import DomainError, ValidationError
from domain_layer.domain_services.walnut_advanced_comparison__domain_service import WalnutAdvancedComparisonDomainService
from domain_layer.domain_services.walnut_comparison__domain_service import WalnutComparisonDomainService
from domain_layer.entities.walnut__entity import WalnutEntity
from domain_layer.value_objects.walnut_comparison__value_object import WalnutComparisonValueObject


class WalnutComparisonEntity:
    """
    Domain entity representing a walnut comparison operation.
    
    Business rules:
    - Contains a list of walnut entities to compare
    - For each main walnut, compares it with all other walnuts
    - Supports different comparison modes: basic_only, advanced_only, or both
    - Generates comparison value objects for each pair
    - Ensures all walnuts have valid dimensions before comparison (for basic)
    - Ensures all walnuts have valid images with embeddings before comparison (for advanced)
    """

    def __new__(cls, walnuts: List[WalnutEntity]) -> "WalnutComparisonEntity":
        raise RuntimeError("WalnutComparisonEntity cannot be instantiated directly. Use WalnutComparisonEntity.create() instead.")

    def __init__(
        self,
        walnuts: List[WalnutEntity],
        comparison_mode: ComparisonModeEnum,
        width_weight: float,
        height_weight: float,
        thickness_weight: float,
        front_weight: float,
        back_weight: float,
        left_weight: float,
        right_weight: float,
        top_weight: float,
        down_weight: float,
        basic_weight: float,
        advanced_weight: float,
        skip_advanced_threshold: float,
    ) -> None:
        self.walnuts: List[WalnutEntity] = walnuts
        self.comparison_mode: ComparisonModeEnum = comparison_mode
        self.width_weight: float = width_weight
        self.height_weight: float = height_weight
        self.thickness_weight: float = thickness_weight
        self.front_weight: float = front_weight
        self.back_weight: float = back_weight
        self.left_weight: float = left_weight
        self.right_weight: float = right_weight
        self.top_weight: float = top_weight
        self.down_weight: float = down_weight
        self.basic_weight: float = basic_weight
        self.advanced_weight: float = advanced_weight
        self.skip_advanced_threshold: float = skip_advanced_threshold
        self._initialized: bool = True

    @staticmethod
    def create(
        walnuts: List[WalnutEntity],
        comparison_mode: ComparisonModeEnum,
        width_weight: float,
        height_weight: float,
        thickness_weight: float,
        front_weight: float,
        back_weight: float,
        left_weight: float,
        right_weight: float,
        top_weight: float,
        down_weight: float,
        basic_weight: float,
        advanced_weight: float,
        skip_advanced_threshold: float,
    ) -> Either["WalnutComparisonEntity", DomainError]:
        """
        Create a WalnutComparisonEntity with validation.
        
        Business rules:
        - Must have at least 2 walnuts
        - For basic mode: all walnuts must have valid dimensions
        - For advanced mode: all walnuts must have valid images with embeddings for all sides
        - For both mode: both conditions must be met
        - Weights must be between 0 and 1
        - Basic weights must sum to approximately 1.0
        - Final weights must sum to approximately 1.0
        """
        if len(walnuts) < 2:
            return Left(ValidationError("Need at least 2 walnuts to perform comparison"))

        # Validate based on comparison mode
        if comparison_mode in (ComparisonModeEnum.BASIC_ONLY, ComparisonModeEnum.BOTH):
            # Validate all walnuts have dimensions
            for walnut in walnuts:
                if walnut.dimensions is None:
                    return Left(ValidationError(f"Walnut {walnut.id} does not have dimensions"))

        if comparison_mode in (ComparisonModeEnum.ADVANCED_ONLY, ComparisonModeEnum.BOTH):
            # Validate all walnuts have images with embeddings for all sides
            for walnut in walnuts:
                if not walnut.images:
                    return Left(ValidationError(f"Walnut {walnut.id} does not have any images"))
                
                # Check that all 6 sides have images with embeddings
                for side_enum in WalnutSideEnum:
                    image_vo = walnut.images.get(side_enum)
                    if image_vo is None:
                        return Left(ValidationError(f"Walnut {walnut.id} is missing image for side {side_enum.value}"))
                    if image_vo.embedding.size == 0:
                        return Left(ValidationError(f"Walnut {walnut.id} image for side {side_enum.value} does not have an embedding"))

        # Validate basic weights
        if not (0.0 <= width_weight <= 1.0):
            return Left(ValidationError(f"Width weight must be between 0 and 1, got {width_weight}"))
        if not (0.0 <= height_weight <= 1.0):
            return Left(ValidationError(f"Height weight must be between 0 and 1, got {height_weight}"))
        if not (0.0 <= thickness_weight <= 1.0):
            return Left(ValidationError(f"Thickness weight must be between 0 and 1, got {thickness_weight}"))

        basic_weight_sum = width_weight + height_weight + thickness_weight
        if abs(basic_weight_sum - 1.0) > 0.01:
            return Left(ValidationError(f"Basic weights must sum to 1.0, got {basic_weight_sum}"))

        # Validate final weights
        if not (0.0 <= basic_weight <= 1.0):
            return Left(ValidationError(f"Basic weight for final similarity must be between 0 and 1, got {basic_weight}"))
        if not (0.0 <= advanced_weight <= 1.0):
            return Left(ValidationError(f"Advanced weight for final similarity must be between 0 and 1, got {advanced_weight}"))

        final_weight_sum = basic_weight + advanced_weight
        if abs(final_weight_sum - 1.0) > 0.01:
            return Left(ValidationError(f"Final weights must sum to 1.0, got {final_weight_sum}"))

        entity = object.__new__(WalnutComparisonEntity)
        entity.__init__(
            walnuts,
            comparison_mode,
            width_weight,
            height_weight,
            thickness_weight,
            front_weight,
            back_weight,
            left_weight,
            right_weight,
            top_weight,
            down_weight,
            basic_weight,
            advanced_weight,
            skip_advanced_threshold,
        )
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
                if i == j:
                    continue

                comparison_vo = self._compare_pair(main_walnut, other_walnut)
                comparisons.append(comparison_vo)

        return comparisons

    def _compare_pair(
        self,
        walnut1: WalnutEntity,
        walnut2: WalnutEntity,
    ) -> WalnutComparisonValueObject:
        """
        Compare a pair of walnuts based on the comparison mode.
        
        Business rules:
        - If mode is BASIC_ONLY: calculate only basic similarity
        - If mode is ADVANCED_ONLY: calculate only advanced similarity
        - If mode is BOTH: calculate both, but skip advanced if basic is below threshold
        """
        # Calculate basic similarity if needed
        basic_similarity: Optional[float] = None
        width_diff_mm: float = 0.0
        height_diff_mm: float = 0.0
        thickness_diff_mm: float = 0.0

        if self.comparison_mode in (ComparisonModeEnum.BASIC_ONLY, ComparisonModeEnum.BOTH):
            width_diff_mm, height_diff_mm, thickness_diff_mm, basic_similarity = (
                WalnutComparisonDomainService.calculate_basic_similarity(
                    walnut1_dimensions=walnut1.dimensions,
                    walnut2_dimensions=walnut2.dimensions,
                    width_weight=self.width_weight,
                    height_weight=self.height_weight,
                    thickness_weight=self.thickness_weight,
                )
            )

        # Calculate advanced similarity if needed
        advanced_similarity: Optional[float] = None
        side_similarities: Dict[WalnutSideEnum, float] = {}

        should_calculate_advanced = False
        if self.comparison_mode == ComparisonModeEnum.ADVANCED_ONLY:
            should_calculate_advanced = True
        elif self.comparison_mode == ComparisonModeEnum.BOTH:
            # Only calculate advanced if basic is above threshold (or if basic wasn't calculated)
            if basic_similarity is None or basic_similarity >= self.skip_advanced_threshold:
                should_calculate_advanced = True

        if should_calculate_advanced:
            side_similarities, advanced_similarity = (
                WalnutAdvancedComparisonDomainService.calculate_advanced_similarity(
                    walnut1_images=walnut1.images,
                    walnut2_images=walnut2.images,
                    front_weight=self.front_weight,
                    back_weight=self.back_weight,
                    left_weight=self.left_weight,
                    right_weight=self.right_weight,
                    top_weight=self.top_weight,
                    down_weight=self.down_weight,
                )
            )

        # Calculate final similarity
        final_similarity = WalnutComparisonDomainService.calculate_final_similarity(
            basic_similarity=basic_similarity,
            advanced_similarity=advanced_similarity,
            basic_weight=self.basic_weight,
            advanced_weight=self.advanced_weight,
        )

        # Create value object
        from common.either import Left, Right

        result = WalnutComparisonValueObject.create(
            walnut_id=walnut1.id,
            compared_walnut_id=walnut2.id,
            width_diff_mm=width_diff_mm,
            height_diff_mm=height_diff_mm,
            thickness_diff_mm=thickness_diff_mm,
            basic_similarity=basic_similarity,
            width_weight=self.width_weight,
            height_weight=self.height_weight,
            thickness_weight=self.thickness_weight,
            front_embedding_score=side_similarities.get(WalnutSideEnum.FRONT),
            back_embedding_score=side_similarities.get(WalnutSideEnum.BACK),
            left_embedding_score=side_similarities.get(WalnutSideEnum.LEFT),
            right_embedding_score=side_similarities.get(WalnutSideEnum.RIGHT),
            top_embedding_score=side_similarities.get(WalnutSideEnum.TOP),
            down_embedding_score=side_similarities.get(WalnutSideEnum.DOWN),
            advanced_similarity=advanced_similarity,
            final_similarity=final_similarity,
        )

        if result.is_left():
            raise ValueError(f"Failed to create comparison: {result.value}")

        return result.value
