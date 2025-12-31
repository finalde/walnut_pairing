# infrastructure_layer/services/walnut_image_service/dimension_measurer.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from common.enums import WalnutSideEnum
from domain_layer.value_objects.image__value_object import ImageValueObject
from PIL import Image, ImageDraw

from .contour_finder import IContourFinder
from .image_segmenter import IImageSegmenter
from .rotated_bounding_box import RotatedBoundingBox


class IDimensionMeasurer(ABC):
    """Interface for dimension measurement."""

    @abstractmethod
    def measure_dimensions(
        self,
        image: np.ndarray,
        image_vo: Optional[ImageValueObject] = None,
        side_enum: Optional[WalnutSideEnum] = None,
        save_intermediate: bool = False,
        background_is_white: bool = True,
        min_contour_size: int = 100,
    ) -> Tuple[float, float]:
        """Measure width and height (in pixels) from a single view."""
        pass


class DimensionMeasurer(IDimensionMeasurer):
    """Measures dimensions from segmented walnut."""

    def __init__(
        self,
        segmenter: IImageSegmenter,
        contour_finder: IContourFinder,
    ) -> None:
        self.segmenter: IImageSegmenter = segmenter
        self.contour_finder: IContourFinder = contour_finder

    def measure_dimensions(
        self,
        image: np.ndarray,
        image_vo: Optional[ImageValueObject] = None,
        side_enum: Optional[WalnutSideEnum] = None,
        save_intermediate: bool = False,
        background_is_white: bool = True,
        min_contour_size: int = 100,
    ) -> Tuple[float, float]:
        """
        Measure width and height (in pixels) from a single view.
        Returns (width_px, height_px) or (0.0, 0.0) if measurement fails.
        """
        # Convert to grayscale
        gray = self._to_grayscale(image)

        if save_intermediate and image_vo and side_enum:
            self._save_image(gray, image_vo, "01_grayscale", side_enum)

        # Segment walnut
        mask = self.segmenter.segment_walnut(gray, background_is_white=background_is_white)
        if mask is None:
            return (0.0, 0.0)

        if save_intermediate and image_vo and side_enum:
            self._save_image(mask, image_vo, "02_mask", side_enum)

        # Find largest contour
        contour = self.contour_finder.find_largest_contour(mask, min_contour_size=min_contour_size)
        if contour is None:
            return (0.0, 0.0)

        # Calculate rotated bounding box
        width_px, height_px = RotatedBoundingBox.from_contour(contour)

        # Save intermediate results
        if save_intermediate and image_vo and side_enum:
            self._save_contour(image, contour, image_vo, "03_contour", side_enum)
            self._save_bbox(image, width_px, height_px, image_vo, "04_bbox", side_enum, contour=contour)

        return (width_px, height_px)

    def _to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Convert image to grayscale."""
        if len(image.shape) == 3:
            return np.dot(image[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.uint8)
        return image.astype(np.uint8)

    def _save_image(self, image_array: np.ndarray, image_vo: ImageValueObject, step_name: str, side_enum: WalnutSideEnum) -> None:
        """Save intermediate image."""
        if image_array.ndim == 2:
            img = Image.fromarray(image_array, mode="L")
        else:
            img = Image.fromarray(image_array)

        output_path = self._get_intermediate_path(image_vo, step_name, side_enum)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path)

    def _save_contour(
        self,
        original_image: np.ndarray,
        contour: np.ndarray,
        image_vo: ImageValueObject,
        step_name: str,
        side_enum: WalnutSideEnum,
    ) -> None:
        """Save image with contour overlay."""
        if original_image.ndim == 3:
            img = Image.fromarray(original_image)
        else:
            img = Image.fromarray(original_image, mode="L").convert("RGB")

        draw = ImageDraw.Draw(img)

        if len(contour) > 0:
            points = [(int(pt[1]), int(pt[0])) for pt in contour]
            if len(points) > 2:
                draw.polygon(points, outline="red", width=2)

        output_path = self._get_intermediate_path(image_vo, step_name, side_enum)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path)

    def _save_bbox(
        self,
        original_image: np.ndarray,
        width_px: float,
        height_px: float,
        image_vo: ImageValueObject,
        step_name: str,
        side_enum: WalnutSideEnum,
        contour: Optional[np.ndarray] = None,
    ) -> None:
        """Save image with bounding box overlay using actual contour position."""
        if original_image.ndim == 3:
            img = Image.fromarray(original_image)
        else:
            img = Image.fromarray(original_image, mode="L").convert("RGB")

        draw = ImageDraw.Draw(img)

        if contour is not None and len(contour) > 0:
            # Calculate bounding box from actual contour position (not assumed center)
            min_y, min_x = contour.min(axis=0)
            max_y, max_x = contour.max(axis=0)
            
            # Use actual bounding box from contour
            bbox = (
                int(min_x),
                int(min_y),
                int(max_x),
                int(max_y),
            )
            
            # Draw bounding box
            draw.rectangle(bbox, outline="green", width=2)
            
            # Calculate and mark center of actual bounding box
            center_x = int((min_x + max_x) / 2)
            center_y = int((min_y + max_y) / 2)
            draw.ellipse([center_x - 5, center_y - 5, center_x + 5, center_y + 5], fill="yellow", outline="yellow")
        else:
            # Fallback: use image center if no contour available
            h, w = original_image.shape[:2]
            center_x, center_y = w // 2, h // 2
            bbox_w, bbox_h = int(width_px), int(height_px)
            
            bbox = (
                center_x - bbox_w // 2,
                center_y - bbox_h // 2,
                center_x + bbox_w // 2,
                center_y + bbox_h // 2,
            )
            draw.rectangle(bbox, outline="green", width=2)
            draw.ellipse([center_x - 5, center_y - 5, center_x + 5, center_y + 5], fill="yellow", outline="yellow")

        output_path = self._get_intermediate_path(image_vo, step_name, side_enum)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path)

    def _get_intermediate_path(self, image_vo: ImageValueObject, step_name: str, side_enum: WalnutSideEnum) -> Path:
        """Generate path for intermediate result file."""
        original_path = Path(image_vo.path)
        side_name = side_enum.value.lower()
        intermediate_dir = original_path.parent / "_intermediate"
        stem = original_path.stem
        suffix = original_path.suffix
        filename = f"{stem}_intermediate_{step_name}_{side_name}{suffix}"
        return intermediate_dir / filename
