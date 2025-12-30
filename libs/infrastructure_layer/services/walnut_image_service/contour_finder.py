# infrastructure_layer/services/walnut_image_service/contour_finder.py
from typing import Optional

import numpy as np


class ContourFinder:
    """Finds and filters contours from binary mask."""

    def __init__(self, min_contour_size: int = 100) -> None:
        self.min_contour_size: int = min_contour_size

    def find_largest_contour(self, mask: np.ndarray) -> Optional[np.ndarray]:
        """
        Find the largest connected component (walnut) in the mask.
        Returns contour as numpy array of points, or None if not found.
        """
        contours = self._find_contours(mask)

        if not contours:
            return None

        # Return the largest contour by area
        largest = max(contours, key=lambda c: self._contour_area(c))

        # Filter out tiny contours (noise)
        if self._contour_area(largest) < self.min_contour_size:
            return None

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
        """Calculate bounding box area of contour."""
        if len(contour) < 3:
            return 0.0
        try:
            min_y, min_x = contour.min(axis=0)
            max_y, max_x = contour.max(axis=0)
            return float((max_x - min_x) * (max_y - min_y))
        except Exception:
            return 0.0
