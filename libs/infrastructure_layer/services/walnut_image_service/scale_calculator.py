# infrastructure_layer/services/walnut_image_service/scale_calculator.py
from typing import Optional


class ScaleCalculator:
    """Calculates pixel-to-mm scaling factor."""

    def __init__(self, default_camera_distance_mm: float = 300.0, default_focal_length_px: float = 1000.0) -> None:
        self.default_camera_distance_mm: float = default_camera_distance_mm
        self.default_focal_length_px: float = default_focal_length_px

    def calculate_scale(self, camera_distance_mm: float, focal_length_px: Optional[float] = None) -> float:
        """
        Calculate mm per pixel using camera distance and focal length.
        Formula: mm_per_px = camera_distance_mm / focal_length_px

        Note: This is a simplified model. For accurate results, use:
        - Physical reference object (coin, ruler)
        - Camera calibration
        """
        focal = focal_length_px or self.default_focal_length_px
        if focal <= 0 or camera_distance_mm <= 0:
            return 0.0

        return camera_distance_mm / focal
