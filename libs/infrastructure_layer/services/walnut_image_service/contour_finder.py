# infrastructure_layer/services/walnut_image_service/contour_finder.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import numpy as np
from common.enums import WalnutSideEnum
from common.logger import get_logger
from domain_layer.value_objects.image__value_object import ImageValueObject
from PIL import Image, ImageDraw


class IContourFinder(ABC):
    """Interface for finding contours."""

    @abstractmethod
    def find_largest_contour(
        self,
        mask: np.ndarray,
        min_contour_size: int = 100,
        original_image: Optional[np.ndarray] = None,
        image_vo: Optional[ImageValueObject] = None,
        side_enum: Optional[WalnutSideEnum] = None,
        save_intermediate: bool = False,
    ) -> Optional[np.ndarray]:
        """Find the largest connected component (walnut) in the mask."""
        pass


class ContourFinder(IContourFinder):
    """Finds and filters contours from binary mask."""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def find_largest_contour(
        self,
        mask: np.ndarray,
        min_contour_size: int = 100,
        original_image: Optional[np.ndarray] = None,
        image_vo: Optional[ImageValueObject] = None,
        side_enum: Optional[WalnutSideEnum] = None,
        save_intermediate: bool = False,
    ) -> Optional[np.ndarray]:
        """
        Find the walnut contour in the mask.
        The walnut is the most circular object (to distinguish from rectangular plates).
        Returns contour as numpy array of points, or None if not found.
        """
        contours = self._find_contours(mask)

        if not contours:
            return None

        # Filter contours by size and calculate circularity
        valid_contours = []
        for i, contour in enumerate(contours):
            area = self._contour_area(contour)
            if area < min_contour_size:
                continue
            
            # Check circularity - walnuts should be roughly circular/elliptical
            # Rectangular plates will have lower circularity
            circularity = self._calculate_circularity(contour, area)
            
            # Log each contour's properties with all details
            self.logger.info(
                "contour_analyzed",
                contour_no=i + 1,
                area=round(area, 2),
                circularity=round(circularity, 4),
                perimeter=round(self._calculate_perimeter(contour), 2),
            )
            
            # Save intermediate image for each contour with metadata in filename
            if save_intermediate and original_image is not None and image_vo and side_enum:
                self._save_contour_image(
                    original_image=original_image,
                    contour=contour,
                    image_vo=image_vo,
                    side_enum=side_enum,
                    contour_no=i + 1,
                    area=area,
                    circularity=circularity,
                )
            
            # Accept all contours above minimum size (we'll select by circularity)
            valid_contours.append((contour, area, circularity, i))

        if not valid_contours:
            self.logger.warning("no_valid_contours", min_contour_size=min_contour_size)
            return None

        # Prioritize circularity over area to distinguish walnut from rectangular plate
        # The walnut should be the most circular object (highest circularity)
        # Use area as tiebreaker if circularity is similar
        # Score = circularity * 1000 + area (circularity is more important)
        best_contour = max(valid_contours, key=lambda x: x[2] * 1000 + x[1])
        
        self.logger.info(
            "walnut_contour_selected",
            contour_no=best_contour[3] + 1,
            area=round(best_contour[1], 2),
            circularity=round(best_contour[2], 4),
            total_contours=len(valid_contours),
        )

        return best_contour[0]

    def _find_contours(self, mask: np.ndarray) -> list[np.ndarray]:
        """Find all contours using flood-fill algorithm."""
        h, w = mask.shape
        visited = np.zeros_like(mask, dtype=bool)
        contours = []

        for y in range(h):
            for x in range(w):
                if mask[y, x] > 0 and not visited[y, x]:
                    contour = self._flood_fill(mask, visited, x, y)
                    if len(contour) > 10:  # Minimum contour points
                        contours.append(contour)

        return contours

    def _flood_fill(self, mask: np.ndarray, visited: np.ndarray, start_x: int, start_y: int) -> np.ndarray:
        """
        Flood-fill to extract connected component, then extract boundary contour.
        Returns only the boundary points (not all filled points).
        """
        h, w = mask.shape
        stack = [(start_x, start_y)]
        filled_area = set()  # Store all filled points

        # First, flood-fill to get all points in the component
        while stack:
            x, y = stack.pop()
            if x < 0 or x >= w or y < 0 or y >= h:
                continue
            if visited[y, x] or mask[y, x] == 0:
                continue

            visited[y, x] = True
            filled_area.add((x, y))

            # 8-connected neighbors
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                stack.append((x + dx, y + dy))

        if not filled_area:
            return np.array([])

        # Extract boundary points (points that have at least one background neighbor)
        boundary_points = []
        for x, y in filled_area:
            # Check if any 8-connected neighbor is background (0) or out of bounds
            is_boundary = False
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nx, ny = x + dx, y + dy
                if nx < 0 or nx >= w or ny < 0 or ny >= h:
                    is_boundary = True
                    break
                if mask[ny, nx] == 0:
                    is_boundary = True
                    break
            
            if is_boundary:
                boundary_points.append([y, x])  # Store as [y, x] for consistency

        if len(boundary_points) < 3:
            return np.array([])

        # Sort boundary points to form a closed contour (trace around the boundary)
        # Use a simple approach: start from top-left, trace clockwise
        boundary_array = np.array(boundary_points)
        if len(boundary_array) == 0:
            return np.array([])

        # Sort by angle from center to get ordered boundary
        center_y = boundary_array[:, 0].mean()
        center_x = boundary_array[:, 1].mean()
        
        # Calculate angles and sort
        angles = np.arctan2(boundary_array[:, 0] - center_y, boundary_array[:, 1] - center_x)
        sorted_indices = np.argsort(angles)
        sorted_boundary = boundary_array[sorted_indices]

        return sorted_boundary

    def _contour_area(self, contour: np.ndarray) -> float:
        """Calculate actual area of contour using shoelace formula."""
        if len(contour) < 3:
            return 0.0
        try:
            # Shoelace formula for polygon area
            x = contour[:, 1]  # x coordinates
            y = contour[:, 0]  # y coordinates
            area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
            return float(area)
        except Exception:
            # Fallback to bounding box area
            min_y, min_x = contour.min(axis=0)
            max_y, max_x = contour.max(axis=0)
            return float((max_x - min_x) * (max_y - min_y))

    def _calculate_circularity(self, contour: np.ndarray, area: float) -> float:
        """
        Calculate circularity of contour.
        Circularity = 4π * area / perimeter^2
        Returns value between 0 (line) and 1 (perfect circle).
        """
        if len(contour) < 3 or area <= 0:
            return 0.0
        
        try:
            # Calculate perimeter
            perimeter = self._calculate_perimeter(contour)
            if perimeter <= 0:
                return 0.0
            
            # Circularity formula: 4π * area / perimeter^2
            circularity = (4.0 * np.pi * area) / (perimeter * perimeter)
            return float(circularity)
        except Exception:
            return 0.0

    def _calculate_perimeter(self, contour: np.ndarray) -> float:
        """Calculate perimeter of contour."""
        if len(contour) < 2:
            return 0.0
        
        try:
            # Calculate Euclidean distance between consecutive points
            diff = np.diff(contour, axis=0)
            distances = np.sqrt(np.sum(diff ** 2, axis=1))
            perimeter = float(np.sum(distances))
            
            # Add distance from last to first point (closed contour)
            if len(contour) > 2:
                last_to_first = np.sqrt(np.sum((contour[-1] - contour[0]) ** 2))
                perimeter += float(last_to_first)
            
            return perimeter
        except Exception:
            return 0.0

    def _save_contour_image(
        self,
        original_image: np.ndarray,
        contour: np.ndarray,
        image_vo: ImageValueObject,
        side_enum: WalnutSideEnum,
        contour_no: int,
        area: float,
        circularity: float,
    ) -> None:
        """Save intermediate image for a contour with metadata in filename."""
        if original_image.ndim == 3:
            img = Image.fromarray(original_image)
        else:
            img = Image.fromarray(original_image, mode="L").convert("RGB")

        draw = ImageDraw.Draw(img)

        # Draw contour
        if len(contour) > 0:
            points = [(int(pt[1]), int(pt[0])) for pt in contour]
            if len(points) > 2:
                draw.polygon(points, outline="red", width=2)

        # Draw bounding box
        min_y, min_x = contour.min(axis=0)
        max_y, max_x = contour.max(axis=0)
        bbox = (int(min_x), int(min_y), int(max_x), int(max_y))
        draw.rectangle(bbox, outline="green", width=2)

        # Mark center
        center_x = int((min_x + max_x) / 2)
        center_y = int((min_y + max_y) / 2)
        draw.ellipse([center_x - 5, center_y - 5, center_x + 5, center_y + 5], fill="yellow", outline="yellow")

        # Add text with metadata
        metadata_text = f"#{contour_no} Area:{int(area)} Circ:{circularity:.3f}"
        draw.text((10, 10), metadata_text, fill="yellow")

        # Generate filename with metadata
        output_path = self._get_contour_intermediate_path(
            image_vo=image_vo,
            side_enum=side_enum,
            contour_no=contour_no,
            area=int(area),
            circularity=circularity,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path)

    def _get_contour_intermediate_path(
        self,
        image_vo: ImageValueObject,
        side_enum: WalnutSideEnum,
        contour_no: int,
        area: int,
        circularity: float,
    ) -> Path:
        """Generate path for contour intermediate result file with metadata."""
        original_path = Path(image_vo.path)
        side_name = side_enum.value.lower()
        intermediate_dir = original_path.parent / "_intermediate"
        stem = original_path.stem
        suffix = original_path.suffix
        # Format: {stem}_contour_{contour_no:02d}_area{area}_circ{circularity:.3f}_{side}{suffix}
        filename = f"{stem}_contour_{contour_no:02d}_area{area}_circ{circularity:.3f}_{side_name}{suffix}"
        return intermediate_dir / filename
