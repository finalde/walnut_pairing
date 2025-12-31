# infrastructure_layer/services/image_object__finder.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import numpy as np
from PIL import Image


@dataclass
class ObjectDetectionResult:
    """Result of object detection in an image."""
    contour: np.ndarray
    area: float
    width_px: float
    height_px: float
    center_x: float
    center_y: float


class IImageObjectFinder(ABC):
    """Interface for finding objects in images."""

    @abstractmethod
    def find_object(
        self,
        image_path: str,
        background_is_white: bool = True,
        intermediate_dir: Optional[str] = None,
    ) -> Optional[ObjectDetectionResult]:
        """
        Find the largest object in an image.
        
        Args:
            image_path: Path to the image file
            background_is_white: Whether background is white (default: True)
            intermediate_dir: Optional directory path to save intermediate images (grayscale, mask, contour)
        
        Returns:
            ObjectDetectionResult with contour, area, dimensions, or None if no object found
        """
        pass

    @abstractmethod
    def find_all_objects(
        self,
        image_path: str,
        background_is_white: bool = True,
        min_contour_size: int = 10,
    ) -> List[ObjectDetectionResult]:
        """
        Find all objects/components in an image.
        
        Args:
            image_path: Path to the image file
            background_is_white: Whether background is white (default: True)
            min_contour_size: Minimum number of points for a valid contour (default: 10)
        
        Returns:
            List of ObjectDetectionResult objects, sorted by area (largest first)
        """
        pass


class ImageObjectFinder(IImageObjectFinder):
    """Simple service for finding objects in images using thresholding and contour detection."""

    def find_object(
        self,
        image_path: str,
        background_is_white: bool = True,
        intermediate_dir: Optional[str] = None,
    ) -> Optional[ObjectDetectionResult]:
        """Find the largest object in an image."""
        # Load image
        img = Image.open(image_path).convert("RGB")
        image = np.array(img)
        h, w = image.shape[:2]

        # Convert to grayscale
        gray = self._to_grayscale(image)
        if intermediate_dir:
            grayscale_path = self._get_intermediate_path(image_path, intermediate_dir, "grayscale")
            self._save_image(gray, grayscale_path)

        # Simple thresholding
        threshold = np.percentile(gray, 50)
        if background_is_white:
            mask = (gray < threshold).astype(np.uint8) * 255
        else:
            mask = (gray > threshold).astype(np.uint8) * 255

        if intermediate_dir:
            mask_path = self._get_intermediate_path(image_path, intermediate_dir, "mask")
            self._save_image(mask, mask_path)

        # Find largest contour
        contour = self._find_largest_contour(mask, h, w)
        if contour is None or len(contour) == 0:
            return None

        if intermediate_dir:
            contour_path = self._get_intermediate_path(image_path, intermediate_dir, "contour")
            self._save_contour(image, contour, contour_path)

        # Calculate bounding box and properties
        min_y, min_x = contour.min(axis=0)
        max_y, max_x = contour.max(axis=0)
        width_px = float(max_x - min_x)
        height_px = float(max_y - min_y)
        center_x = float((min_x + max_x) / 2)
        center_y = float((min_y + max_y) / 2)
        area = float(len(contour))

        return ObjectDetectionResult(
            contour=contour,
            area=area,
            width_px=width_px,
            height_px=height_px,
            center_x=center_x,
            center_y=center_y,
        )

    def find_all_objects(
        self,
        image_path: str,
        background_is_white: bool = True,
        min_contour_size: int = 10,
    ) -> List[ObjectDetectionResult]:
        """Find all objects/components in an image."""
        # Load image
        img = Image.open(image_path).convert("RGB")
        image = np.array(img)
        h, w = image.shape[:2]

        # Convert to grayscale
        gray = self._to_grayscale(image)

        # Simple thresholding
        threshold = np.percentile(gray, 50)
        if background_is_white:
            mask = (gray < threshold).astype(np.uint8) * 255
        else:
            mask = (gray > threshold).astype(np.uint8) * 255

        # Find all contours
        all_contours = self._find_all_contours(mask, h, w, min_contour_size)

        # Convert contours to ObjectDetectionResult objects
        results = []
        for contour in all_contours:
            if len(contour) == 0:
                continue

            min_y, min_x = contour.min(axis=0)
            max_y, max_x = contour.max(axis=0)
            width_px = float(max_x - min_x)
            height_px = float(max_y - min_y)
            center_x = float((min_x + max_x) / 2)
            center_y = float((min_y + max_y) / 2)
            area = float(len(contour))

            results.append(
                ObjectDetectionResult(
                    contour=contour,
                    area=area,
                    width_px=width_px,
                    height_px=height_px,
                    center_x=center_x,
                    center_y=center_y,
                )
            )

        # Sort by area (largest first)
        results.sort(key=lambda x: x.area, reverse=True)

        return results

    def _find_all_contours(self, mask: np.ndarray, h: int, w: int, min_contour_size: int = 10) -> List[np.ndarray]:
        """Find all contours using simple flood-fill."""
        visited = np.zeros_like(mask, dtype=bool)
        all_contours = []

        for y in range(h):
            for x in range(w):
                if mask[y, x] > 0 and not visited[y, x]:
                    contour = self._flood_fill(mask, visited, x, y, h, w)
                    if len(contour) > min_contour_size:
                        all_contours.append(contour)

        return all_contours

    def _to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Convert image to grayscale."""
        if len(image.shape) == 3:
            return np.dot(image[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.uint8)
        return image.astype(np.uint8)

    def _find_largest_contour(self, mask: np.ndarray, h: int, w: int) -> Optional[np.ndarray]:
        """Find largest contour using simple flood-fill."""
        visited = np.zeros_like(mask, dtype=bool)
        largest_contour = None
        largest_area = 0

        for y in range(h):
            for x in range(w):
                if mask[y, x] > 0 and not visited[y, x]:
                    contour = self._flood_fill(mask, visited, x, y, h, w)
                    if len(contour) > 10:
                        area = len(contour)
                        if area > largest_area:
                            largest_area = area
                            largest_contour = contour

        return largest_contour

    def _flood_fill(self, mask: np.ndarray, visited: np.ndarray, start_x: int, start_y: int, h: int, w: int) -> np.ndarray:
        """Simple flood-fill to extract connected component."""
        stack = [(start_x, start_y)]
        points = []

        while stack:
            x, y = stack.pop()
            if x < 0 or x >= w or y < 0 or y >= h:
                continue
            if visited[y, x] or mask[y, x] == 0:
                continue

            visited[y, x] = True
            points.append([y, x])

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                stack.append((x + dx, y + dy))

        return np.array(points) if points else np.array([])

    def _save_image(self, image_array: np.ndarray, output_path: str) -> None:
        """Save image to specified path."""
        if image_array.ndim == 2:
            img = Image.fromarray(image_array, mode="L")
        else:
            img = Image.fromarray(image_array)

        from pathlib import Path

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(path)

    def _save_contour(self, image: np.ndarray, contour: np.ndarray, output_path: str) -> None:
        """Save image with contour overlay to specified path."""
        if image.ndim == 3:
            img = Image.fromarray(image)
        else:
            img = Image.fromarray(image, mode="L").convert("RGB")

        from PIL import ImageDraw

        draw = ImageDraw.Draw(img)
        if len(contour) > 0:
            points = [(int(pt[1]), int(pt[0])) for pt in contour]
            if len(points) > 2:
                draw.polygon(points, outline="red", width=2)

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(path)

    def _get_intermediate_path(self, image_path: str, intermediate_dir: str, step_name: str) -> str:
        """Generate path for intermediate result file."""
        original_path = Path(image_path)
        intermediate_path = Path(intermediate_dir)
        stem = original_path.stem
        suffix = original_path.suffix
        filename = f"{stem}_intermediate_{step_name}{suffix}"
        return str(intermediate_path / filename)

