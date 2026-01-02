# domain_layer/domain_services/walnut_comparison__domain_service.py
from domain_layer.value_objects.walnut_comparison__value_object import WalnutComparisonValueObject
from domain_layer.value_objects.walnut_dimension__value_object import WalnutDimensionValueObject


class WalnutComparisonDomainService:
    """
    Domain service for walnut comparison business logic.
    
    Contains business rules about how walnuts are compared and similarity scores are calculated.
    """

    # Similarity score weights (must sum to 1.0)
    WIDTH_WEIGHT: float = 0.40   # 宽（正反面图最宽距离平均值）- 权重40%
    HEIGHT_WEIGHT: float = 0.35  # 高（正反左右图纵向高平均值）- 权重35%
    THICKNESS_WEIGHT: float = 0.25  # 肚（厚度顶底面棱水平视角纵向高平均值）- 权重25%

    @staticmethod
    def calculate_comparison(
        walnut1_id: str,
        walnut1_dimensions: WalnutDimensionValueObject,
        walnut2_id: str,
        walnut2_dimensions: WalnutDimensionValueObject,
    ) -> WalnutComparisonValueObject:
        """
        Calculate comparison between two walnuts.
        
        Business rules:
        - Calculate absolute differences for width, height, and thickness
        - Calculate similarity score using weighted differences
        - Similarity score formula:
          score = (width_diff * WIDTH_WEIGHT + height_diff * HEIGHT_WEIGHT + thickness_diff * THICKNESS_WEIGHT)
          where each diff is normalized as percentage of average dimension
        
        Args:
            walnut1_id: ID of first walnut
            walnut1_dimensions: Dimensions of first walnut
            walnut2_id: ID of second walnut
            walnut2_dimensions: Dimensions of second walnut
        
        Returns:
            WalnutComparisonValueObject with differences and similarity score
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
        similarity_score = 1.0 - (
            WalnutComparisonDomainService.WIDTH_WEIGHT * width_diff_normalized +
            WalnutComparisonDomainService.HEIGHT_WEIGHT * height_diff_normalized +
            WalnutComparisonDomainService.THICKNESS_WEIGHT * thickness_diff_normalized
        )

        # Ensure score is between 0 and 1 (clip if necessary)
        similarity_score = min(max(similarity_score, 0.0), 1.0)

        # Create value object (validation will happen in create method)
        from common.either import Left, Right
        
        result = WalnutComparisonValueObject.create(
            walnut_id=walnut1_id,
            compared_walnut_id=walnut2_id,
            width_diff_mm=width_diff_mm,
            height_diff_mm=height_diff_mm,
            thickness_diff_mm=thickness_diff_mm,
            similarity_score=similarity_score,
        )

        # Since we've validated inputs, this should always be Right
        # But we need to handle the Either type
        if result.is_left():
            raise ValueError(f"Failed to create comparison: {result.value}")
        
        return result.value

