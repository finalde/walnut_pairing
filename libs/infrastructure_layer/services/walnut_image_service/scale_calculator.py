# infrastructure_layer/services/walnut_image_service/scale_calculator.py
from typing import Optional


class ScaleCalculator:
    """Calculates pixel-to-mm scaling factor."""

    def calculate_scale(self, camera_distance_mm: float, focal_length_px: float = 1000.0) -> float:
        """
        Calculate mm per pixel using camera distance and focal length.
        Formula: mm_per_px = camera_distance_mm / focal_length_px

        Note: This is a simplified model. For accurate results, use:
        - Physical reference object (coin, ruler)
        - Camera calibration
        """
        if focal_length_px <= 0 or camera_distance_mm <= 0:
            return 0.0

        return camera_distance_mm / focal_length_px
