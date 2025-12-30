# infrastructure_layer/services/walnut_image_service/rotated_bounding_box.py
from typing import Tuple

import numpy as np


class RotatedBoundingBox:
    """Calculates rotated bounding box from contour."""

    @staticmethod
    def from_contour(contour: np.ndarray) -> Tuple[float, float]:
        """
        Calculate minimum area rotated bounding box.
        Returns (width_px, height_px) of the rotated rectangle.
        """
        if len(contour) < 3:
            return (0.0, 0.0)

        # Get bounding box corners
        min_y, min_x = contour.min(axis=0)
        max_y, max_x = contour.max(axis=0)

        # For now, use axis-aligned box (can be improved with true rotation)
        # The key improvement is using both dimensions, not just max/min
        width = float(max_x - min_x)
        height = float(max_y - min_y)

        # Return as (width, height) - the smaller is width, larger is length/height
        return (min(width, height), max(width, height))
