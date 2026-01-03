# domain_layer/domain_services/walnut_comparison__domain_service.py
from typing import Dict, Optional

from common.enums import WalnutSideEnum
from domain_layer.value_objects.walnut_comparison__value_object import WalnutComparisonValueObject
from domain_layer.value_objects.walnut_dimension__value_object import WalnutDimensionValueObject
from domain_layer.value_objects.walnut_image__value_object import WalnutImageValueObject
from domain_layer.domain_services.walnut_advanced_comparison__domain_service import WalnutAdvancedComparisonDomainService


class WalnutComparisonDomainService:
    """
    Domain service for walnut comparison business logic.
    
    Contains business rules about how walnuts are compared and similarity scores are calculated.
    """

    @staticmethod
    def calculate_basic_similarity(
        walnut1_dimensions: WalnutDimensionValueObject,
        walnut2_dimensions: WalnutDimensionValueObject,
        width_weight: float,
        height_weight: float,
        thickness_weight: float,
    ) -> tuple[float, float, float, float]:
        """
        Calculate basic similarity based on dimensions.
        
        Returns:
            Tuple of (width_diff_mm, height_diff_mm, thickness_diff_mm, basic_similarity)
        """
        """
        Calculate basic similarity based on dimensions.
        
        Business rules:
        - Calculate absolute differences for width, height, and thickness
        - Calculate similarity score using weighted differences
        - Similarity score formula:
          score = 1.0 - (width_diff_normalized * width_weight + height_diff_normalized * height_weight + thickness_diff_normalized * thickness_weight)
          where each diff is normalized as percentage of average dimension
        
        Args:
            walnut1_dimensions: Dimensions of first walnut
            walnut2_dimensions: Dimensions of second walnut
            width_weight: Weight for width difference
            height_weight: Weight for height difference
            thickness_weight: Weight for thickness difference
        
        Returns:
            Tuple of (width_diff_mm, height_diff_mm, thickness_diff_mm, basic_similarity)
        """
        # Calculate absolute differences
        width_diff_mm = walnut1_dimensions.width_mm - walnut2_dimensions.width_mm
        height_diff_mm = walnut1_dimensions.height_mm - walnut2_dimensions.height_mm
        thickness_diff_mm = walnut1_dimensions.thickness_mm - walnut2_dimensions.thickness_mm

        abs_width_diff_mm = abs(width_diff_mm)
        abs_height_diff_mm = abs(height_diff_mm)
        abs_thickness_diff_mm = abs(thickness_diff_mm)

        # Calculate average dimensions for normalization
        avg_width = (walnut1_dimensions.width_mm + walnut2_dimensions.width_mm) / 2.0
        avg_height = (walnut1_dimensions.height_mm + walnut2_dimensions.height_mm) / 2.0
        avg_thickness = (walnut1_dimensions.thickness_mm + walnut2_dimensions.thickness_mm) / 2.0

        # Normalize differences as percentages (avoid division by zero)
        width_diff_normalized = abs_width_diff_mm / avg_width if avg_width > 0 else 0.0
        height_diff_normalized = abs_height_diff_mm / avg_height if avg_height > 0 else 0.0
        thickness_diff_normalized = abs_thickness_diff_mm / avg_thickness if avg_thickness > 0 else 0.0

        # Calculate weighted similarity score
        basic_similarity = 1.0 - (
            width_weight * width_diff_normalized +
            height_weight * height_diff_normalized +
            thickness_weight * thickness_diff_normalized
        )

        # Ensure score is between 0 and 1 (clip if necessary)
        basic_similarity = min(max(basic_similarity, 0.0), 1.0)

        return width_diff_mm, height_diff_mm, thickness_diff_mm, basic_similarity

    @staticmethod
    def calculate_final_similarity(
        basic_similarity: Optional[float],
        advanced_similarity: Optional[float],
        basic_weight: float,
        advanced_weight: float,
    ) -> float:
        """
        Calculate final similarity by combining basic and advanced similarities.
        
        Business rules:
        - If only basic is available, use basic
        - If only advanced is available, use advanced
        - If both are available, use weighted combination
        
        Args:
            basic_similarity: Basic similarity score (can be None)
            advanced_similarity: Advanced similarity score (can be None)
            basic_weight: Weight for basic similarity
            advanced_weight: Weight for advanced similarity
        
        Returns:
            Final similarity score between 0 and 1
        """
        if basic_similarity is None and advanced_similarity is None:
            return 0.0
        
        if basic_similarity is None:
            return advanced_similarity
        
        if advanced_similarity is None:
            return basic_similarity
        
        # Both are available, use weighted combination
        final_similarity = (
            basic_weight * basic_similarity +
            advanced_weight * advanced_similarity
        )
        
        # Ensure score is between 0 and 1 (clip if necessary)
        return min(max(final_similarity, 0.0), 1.0)

