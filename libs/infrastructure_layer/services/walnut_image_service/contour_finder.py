# infrastructure_layer/services/walnut_image_service/contour_finder.py
from abc import ABC, abstractmethod
from typing import Optional

import numpy as np


class IContourFinder(ABC):
    """Interface for finding contours."""

    @abstractmethod
    def find_largest_contour(self, mask: np.ndarray, min_contour_size: int = 100) -> Optional[np.ndarray]:
        """Find the largest connected component (walnut) in the mask."""
        pass


class ContourFinder(IContourFinder):
    """Finds and filters contours from binary mask."""

    def find_largest_contour(self, mask: np.ndarray, min_contour_size: int = 100) -> Optional[np.ndarray]:
        """
        Find the largest connected component (walnut) in the mask.
        The walnut is assumed to be the largest close-to-circular object.
        Returns contour as numpy array of points, or None if not found.
        """
        contours = self._find_contours(mask)

        if not contours:
            return None

        # Filter contours by size and circularity
        valid_contours = []
        for contour in contours:
            area = self._contour_area(contour)
            if area < min_contour_size:
                continue
            
            # Check circularity - walnuts should be roughly circular/elliptical
            circularity = self._calculate_circularity(contour, area)
            # Accept contours with circularity > 0.3 (allows for ellipses)
            # Perfect circle = 1.0, line = 0.0
            if circularity > 0.3:
                valid_contours.append((contour, area, circularity))

        if not valid_contours:
            return None

        # Return the largest contour by area (among circular ones)
        # This ensures we get the walnut (largest circular object) regardless of position
        largest = max(valid_contours, key=lambda x: x[1])[0]

        return largest

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
        """Flood-fill to extract connected component."""
        h, w = mask.shape
        stack = [(start_x, start_y)]
        contour = []

        while stack:
            x, y = stack.pop()
            if x < 0 or x >= w or y < 0 or y >= h:
                continue
            if visited[y, x] or mask[y, x] == 0:
                continue

            visited[y, x] = True
            contour.append([y, x])

            # 8-connected neighbors
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                stack.append((x + dx, y + dy))

        return np.array(contour) if contour else np.array([])

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
