# domain_layer/domain_services/dimension__domain_service.py
from typing import Dict

import numpy as np

from common.enums import WalnutSideEnum


class DimensionDomainService:
    """
    Domain service for dimension-related business logic.
    Contains business rules about how dimensions are derived from views.
    """

    # Business rule: minimum number of valid views required per dimension
    MIN_VALID_VIEWS: int = 2

    # Business rule: valid walnut dimension range (mm)
    MIN_DIMENSION_MM: float = 20.0
    MAX_DIMENSION_MM: float = 50.0

    @staticmethod
    def aggregate_dimensions(
        pixel_measurements: Dict[str, list[float]],
        mm_per_pixel: float,
        min_valid_views: int = MIN_VALID_VIEWS,
    ) -> Dict[str, float]:
        """
        Aggregate pixel measurements into final dimensions in mm.
        
        Business rule: Use median for robustness against outliers.
        Business rule: Require minimum number of valid views.
        """
        result = {}

        for dimension in ["length", "width", "height"]:
            pixel_values = pixel_measurements.get(dimension, [])
            # Filter out zeros (failed measurements)
            valid_pixel_values = [v for v in pixel_values if v > 0]

            if len(valid_pixel_values) < min_valid_views:
                result[dimension] = 0.0
            else:
                # Use median for robustness (business rule)
                median_pixels = float(np.median(valid_pixel_values))
                result[dimension] = median_pixels * mm_per_pixel

        return result

    @staticmethod
    def get_view_contribution(side: WalnutSideEnum) -> Dict[str, str]:
        """
        Business rule: What each view contributes to which dimension.
        Returns dict mapping dimension name to which measurement (width/height) to use.
        """
        mapping = {
            WalnutSideEnum.FRONT: {"length": "width", "height": "height"},
            WalnutSideEnum.BACK: {"length": "width", "height": "height"},
            WalnutSideEnum.LEFT: {"width": "width", "height": "height"},
            WalnutSideEnum.RIGHT: {"width": "width", "height": "height"},
            WalnutSideEnum.TOP: {"length": "width", "width": "height"},
            WalnutSideEnum.DOWN: {"length": "width", "width": "height"},
        }
        return mapping.get(side, {})

