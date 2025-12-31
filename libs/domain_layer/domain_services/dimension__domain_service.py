# domain_layer/domain_services/dimension__domain_service.py
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
from common.enums import WalnutSideEnum


@dataclass
class ViewMeasurement:
    """Measurement from a single view."""
    side: WalnutSideEnum
    width_px: float
    height_px: float
    camera_distance_mm: float


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
    def calculate_dimensions_from_measurements(
        measurements: List[ViewMeasurement],
        focal_length_px: float,
    ) -> Tuple[float, float, float]:
        """
        Calculate walnut dimensions from view measurements.
        
        Business rules:
        - Maps each view to dimensions based on view orientation
        - Aggregates measurements using median for robustness
        - Requires minimum number of valid views per dimension
        
        Args:
            measurements: List of measurements from different views
            focal_length_px: Camera focal length in pixels
            
        Returns:
            Tuple of (x_mm, y_mm, z_mm)
        """
        # Map measurements to dimensions based on view
        # Mapping: length -> x, width -> y, height -> z
        pixel_measurements: Dict[str, List[float]] = {"x": [], "y": [], "z": []}
        camera_distances: List[float] = []
        
        for measurement in measurements:
            
            camera_distances.append(measurement.camera_distance_mm)
            
            # Business rule: Map each view to dimensions
            # length -> x, width -> y, height -> z
            contribution = DimensionDomainService._get_view_contribution(measurement.side)
            
            for axis_name, measurement_type in contribution.items():
                if measurement_type == "width":
                    pixel_measurements[axis_name].append(measurement.width_px)
                elif measurement_type == "height":
                    pixel_measurements[axis_name].append(measurement.height_px)
        
        if not camera_distances:
            return (0.0, 0.0, 0.0)
        
        # Calculate scale (mm per pixel)
        avg_distance = sum(camera_distances) / len(camera_distances)
        mm_per_px = avg_distance / focal_length_px if focal_length_px > 0 else 0.0
        if mm_per_px <= 0:
            return (0.0, 0.0, 0.0)
        
        # Aggregate dimensions
        dimensions_mm = DimensionDomainService.aggregate_dimensions(
            pixel_measurements, mm_per_px
        )
        
        return (
            dimensions_mm["x"],
            dimensions_mm["y"],
            dimensions_mm["z"],
        )

    @staticmethod
    def aggregate_dimensions(
        pixel_measurements: Dict[str, List[float]],
        mm_per_pixel: float,
        min_valid_views: int = MIN_VALID_VIEWS,
    ) -> Dict[str, float]:
        """
        Aggregate pixel measurements into final dimensions in mm.

        Business rule: Use median for robustness against outliers.
        Business rule: Require minimum number of valid views.
        """
        result = {}

        for axis in ["x", "y", "z"]:
            pixel_values = pixel_measurements.get(axis, [])
            # Filter out zeros (failed measurements)
            valid_pixel_values = [v for v in pixel_values if v > 0]

            if len(valid_pixel_values) < min_valid_views:
                result[axis] = 0.0
            else:
                # Use median for robustness (business rule)
                median_pixels = float(np.median(valid_pixel_values))
                result[axis] = median_pixels * mm_per_pixel

        return result

    @staticmethod
    def _get_view_contribution(side: WalnutSideEnum) -> Dict[str, str]:
        """
        Business rule: What each view contributes to which dimension.
        Returns dict mapping axis name (x, y, z) to which measurement (width/height) to use.
        Mapping: length -> x, width -> y, height -> z
        """
        mapping = {
            WalnutSideEnum.FRONT: {"x": "width", "z": "height"},
            WalnutSideEnum.BACK: {"x": "width", "z": "height"},
            WalnutSideEnum.LEFT: {"y": "width", "z": "height"},
            WalnutSideEnum.RIGHT: {"y": "width", "z": "height"},
            WalnutSideEnum.TOP: {"x": "width", "y": "height"},
            WalnutSideEnum.DOWN: {"x": "width", "y": "height"},
        }
        return mapping.get(side, {})
