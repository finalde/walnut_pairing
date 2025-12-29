# infrastructure_layer/services/walnut_image__service.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw

from common.enums import WalnutSideEnum
from domain_layer.value_objects.image__value_object import ImageValueObject


class IWalnutImageService(ABC):
    @abstractmethod
    def estimate_dimensions(
        self,
        images: Dict[WalnutSideEnum, ImageValueObject],
        camera_quality_factor: Optional[float] = None,
        min_dimension_mm: Optional[float] = None,
        max_dimension_mm: Optional[float] = None,
        save_intermediate_results: bool = False,
    ) -> Tuple[float, float, float]:
        """
        Estimate walnut dimensions (length, width, height) from 6 side images.

        Args:
            images: Dictionary mapping WalnutSideEnum to ImageValueObjects
                Must contain all 6 sides: FRONT, BACK, LEFT, RIGHT, TOP, DOWN
            camera_quality_factor: Quality factor (0.0-1.0) affecting edge detection sensitivity.
                - 0.0 = Low quality camera (noisy images, requires higher edge threshold to filter noise)
                - 1.0 = High quality camera (clean images, can use lower edge threshold for better detection)
                - This is converted to edge_threshold: edge_threshold = 1.0 - quality_factor
                - Higher quality_factor -> Lower edge_threshold -> More sensitive edge detection -> More edges detected
                - Lower quality_factor -> Higher edge_threshold -> Less sensitive edge detection -> Fewer edges detected (filters noise)
                - Default: Uses service's default_camera_quality_factor
            min_dimension_mm: Optional minimum dimension in mm for validation
            max_dimension_mm: Optional maximum dimension in mm for validation
            save_intermediate_results: If True, saves intermediate processing images
                (grayscale, edges, contours, bounding boxes) to _intermediate folder
                under each image's original path. Files are named with pattern:
                {original_name}_intermediate_{step}_{side}.png

        Returns:
            Tuple of (length_mm, width_mm, height_mm)
        """
        pass


class WalnutImageService(IWalnutImageService):
    def __init__(
        self,
        default_camera_distance_mm: float = 300.0,
        default_camera_quality_factor: float = 0.7,
        default_walnut_size_mm: float = 30.0,
    ) -> None:
        self.default_camera_distance_mm: float = default_camera_distance_mm
        self.default_camera_quality_factor: float = default_camera_quality_factor
        self.default_walnut_size_mm: float = default_walnut_size_mm

    def estimate_dimensions(
        self,
        images: Dict[WalnutSideEnum, ImageValueObject],
        camera_quality_factor: Optional[float] = None,
        min_dimension_mm: Optional[float] = None,
        max_dimension_mm: Optional[float] = None,
        save_intermediate_results: bool = False,
    ) -> Tuple[float, float, float]:
        image_dict = {}
        camera_distances: Dict[WalnutSideEnum, float] = {}
        for side_enum, image_vo in images.items():
            image_dict[side_enum] = Image.open(image_vo.path).convert("RGB")
            camera_distances[side_enum] = image_vo.camera_distance_mm or self.default_camera_distance_mm

        quality_factor = camera_quality_factor or self.default_camera_quality_factor
        edge_threshold = 1.0 - quality_factor

        pixel_dimensions = self._estimate_pixel_dimensions(
            image_dict, edge_threshold, images if save_intermediate_results else None
        )

        scales = self._estimate_scales_from_camera_distances(image_dict, pixel_dimensions, camera_distances)

        length_mm = pixel_dimensions["length"] * scales["length"]
        width_mm = pixel_dimensions["width"] * scales["width"]
        height_mm = pixel_dimensions["height"] * scales["height"]

        if min_dimension_mm is not None:
            length_mm = max(length_mm, min_dimension_mm)
            width_mm = max(width_mm, min_dimension_mm)
            height_mm = max(height_mm, min_dimension_mm)

        if max_dimension_mm is not None:
            length_mm = min(length_mm, max_dimension_mm)
            width_mm = min(width_mm, max_dimension_mm)
            height_mm = min(height_mm, max_dimension_mm)

        return (length_mm, width_mm, height_mm)

    def _estimate_pixel_dimensions(
        self,
        images: Dict[WalnutSideEnum, Image.Image],
        edge_threshold: float,
        image_vos: Optional[Dict[WalnutSideEnum, ImageValueObject]] = None,
    ) -> Dict[str, float]:
        front = np.array(images[WalnutSideEnum.FRONT])
        back = np.array(images[WalnutSideEnum.BACK])
        left = np.array(images[WalnutSideEnum.LEFT])
        right = np.array(images[WalnutSideEnum.RIGHT])
        top = np.array(images[WalnutSideEnum.TOP])
        down = np.array(images[WalnutSideEnum.DOWN])

        length_px = self._estimate_dimension_from_orthogonal_views(
            [front, back],
            [left, right],
            [top, down],
            edge_threshold,
            image_vos,
            [WalnutSideEnum.FRONT, WalnutSideEnum.BACK, WalnutSideEnum.LEFT, WalnutSideEnum.RIGHT, WalnutSideEnum.TOP, WalnutSideEnum.DOWN],
        )
        width_px = self._estimate_dimension_from_orthogonal_views(
            [left, right],
            [front, back],
            [top, down],
            edge_threshold,
            image_vos,
            [WalnutSideEnum.LEFT, WalnutSideEnum.RIGHT, WalnutSideEnum.FRONT, WalnutSideEnum.BACK, WalnutSideEnum.TOP, WalnutSideEnum.DOWN],
        )
        height_px = self._estimate_dimension_from_orthogonal_views(
            [top, down],
            [front, back],
            [left, right],
            edge_threshold,
            image_vos,
            [WalnutSideEnum.TOP, WalnutSideEnum.DOWN, WalnutSideEnum.FRONT, WalnutSideEnum.BACK, WalnutSideEnum.LEFT, WalnutSideEnum.RIGHT],
        )

        return {"length": length_px, "width": width_px, "height": height_px}

    def _estimate_dimension_from_orthogonal_views(
        self,
        primary_views: list[np.ndarray],
        side_views: list[np.ndarray],
        top_views: list[np.ndarray],
        edge_threshold: float,
        image_vos: Optional[Dict[WalnutSideEnum, ImageValueObject]] = None,
        primary_sides: Optional[list[WalnutSideEnum]] = None,
    ) -> float:
        measurements = []

        side_enums_for_views = []
        if image_vos and primary_sides:
            side_enums_for_views = primary_sides + [
                s for s in [WalnutSideEnum.LEFT, WalnutSideEnum.RIGHT, WalnutSideEnum.TOP, WalnutSideEnum.DOWN] if s not in primary_sides
            ]

        view_idx = 0
        for view in primary_views:
            side_enum = side_enums_for_views[view_idx] if image_vos and view_idx < len(side_enums_for_views) else None
            dim = self._measure_primary_dimension(view, edge_threshold, image_vos, side_enum)
            if dim > 0:
                measurements.append(dim)
            view_idx += 1

        for view in side_views:
            side_enum = side_enums_for_views[view_idx] if image_vos and view_idx < len(side_enums_for_views) else None
            dim = self._measure_secondary_dimension(view, edge_threshold, image_vos, side_enum)
            if dim > 0:
                measurements.append(dim)
            view_idx += 1

        for view in top_views:
            side_enum = side_enums_for_views[view_idx] if image_vos and view_idx < len(side_enums_for_views) else None
            dim = self._measure_secondary_dimension(view, edge_threshold, image_vos, side_enum)
            if dim > 0:
                measurements.append(dim)
            view_idx += 1

        if not measurements:
            return 0.0

        return float(np.median(measurements))

    def _measure_primary_dimension(
        self,
        image: np.ndarray,
        edge_threshold: float,
        image_vos: Optional[Dict[WalnutSideEnum, ImageValueObject]] = None,
        side_enum: Optional[WalnutSideEnum] = None,
    ) -> float:
        """
        Measure the primary dimension (largest) of the walnut in the image.
        The walnut is expected to be centered in the image. If the detected bounding box
        is too far from the center (>30% of image size), it's likely not the walnut.
        """
        gray = self._to_grayscale(image)
        edges = self._detect_edges(gray, edge_threshold)
        contours = self._find_contours(edges)

        if image_vos and side_enum:
            self._save_intermediate_image(gray, image_vos[side_enum], "01_grayscale")
            self._save_intermediate_image(edges, image_vos[side_enum], "02_edges")

        if not contours:
            return float(max(image.shape[0], image.shape[1]))

        largest_contour = max(contours, key=lambda c: self._contour_area(c))
        bbox = self._bounding_box(largest_contour)

        if image_vos and side_enum:
            self._save_intermediate_contour(image, contours, largest_contour, image_vos[side_enum], "03_contours")
            self._save_intermediate_bbox(image, bbox, image_vos[side_enum], "04_bounding_box")

        center_x = image.shape[1] // 2
        center_y = image.shape[0] // 2
        bbox_center_x = (bbox[0] + bbox[2]) // 2
        bbox_center_y = (bbox[1] + bbox[3]) // 2

        if abs(bbox_center_x - center_x) > image.shape[1] * 0.3 or abs(bbox_center_y - center_y) > image.shape[0] * 0.3:
            return float(max(image.shape[0], image.shape[1]))

        return float(max(bbox[2] - bbox[0], bbox[3] - bbox[1]))

    def _measure_secondary_dimension(
        self,
        image: np.ndarray,
        edge_threshold: float,
        image_vos: Optional[Dict[WalnutSideEnum, ImageValueObject]] = None,
        side_enum: Optional[WalnutSideEnum] = None,
    ) -> float:
        """
        Measure the secondary dimension (smallest) of the walnut in the image.
        The walnut is expected to be centered in the image. If the detected bounding box
        is too far from the center (>30% of image size), it's likely not the walnut.
        """
        gray = self._to_grayscale(image)
        edges = self._detect_edges(gray, edge_threshold)
        contours = self._find_contours(edges)

        if image_vos and side_enum:
            self._save_intermediate_image(gray, image_vos[side_enum], "01_grayscale")
            self._save_intermediate_image(edges, image_vos[side_enum], "02_edges")

        if not contours:
            return 0.0

        largest_contour = max(contours, key=lambda c: self._contour_area(c))
        bbox = self._bounding_box(largest_contour)

        if image_vos and side_enum:
            self._save_intermediate_contour(image, contours, largest_contour, image_vos[side_enum], "03_contours")
            self._save_intermediate_bbox(image, bbox, image_vos[side_enum], "04_bounding_box")

        center_x = image.shape[1] // 2
        center_y = image.shape[0] // 2
        bbox_center_x = (bbox[0] + bbox[2]) // 2
        bbox_center_y = (bbox[1] + bbox[3]) // 2

        if abs(bbox_center_x - center_x) > image.shape[1] * 0.3 or abs(bbox_center_y - center_y) > image.shape[0] * 0.3:
            return 0.0

        return float(min(bbox[2] - bbox[0], bbox[3] - bbox[1]))

    def _to_grayscale(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 3:
            return np.dot(image[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.uint8)
        return image.astype(np.uint8)

    def _detect_edges(self, gray: np.ndarray, edge_threshold: float) -> np.ndarray:
        """
        Detect edges using Sobel operator.

        edge_threshold: Threshold for edge detection (0.0-1.0)
            - Lower threshold (e.g., 0.1) = More sensitive, detects more edges (good for high quality cameras)
            - Higher threshold (e.g., 0.9) = Less sensitive, detects fewer edges (good for low quality/noisy cameras)
            - Formula: edge_threshold = 1.0 - camera_quality_factor
            - Example: quality_factor=0.7 -> edge_threshold=0.3 (moderate sensitivity)
        """
        kernel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
        kernel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)

        h, w = gray.shape
        sobel_x = np.zeros_like(gray, dtype=np.float32)
        sobel_y = np.zeros_like(gray, dtype=np.float32)

        for y in range(1, h - 1):
            for x in range(1, w - 1):
                patch = gray[y - 1 : y + 2, x - 1 : x + 2].astype(np.float32)
                sobel_x[y, x] = np.sum(patch * kernel_x)
                sobel_y[y, x] = np.sum(patch * kernel_y)

        magnitude = np.hypot(sobel_x, sobel_y)
        threshold = magnitude.max() * edge_threshold
        return (magnitude > threshold).astype(np.uint8) * 255

    def _find_contours(self, edges: np.ndarray) -> list[np.ndarray]:
        h, w = edges.shape
        visited = np.zeros_like(edges, dtype=bool)
        contours = []

        for y in range(h):
            for x in range(w):
                if edges[y, x] > 0 and not visited[y, x]:
                    contour = self._flood_fill(edges, visited, x, y)
                    if len(contour) > 10:
                        contours.append(contour)

        return contours

    def _flood_fill(self, edges: np.ndarray, visited: np.ndarray, start_x: int, start_y: int) -> np.ndarray:
        h, w = edges.shape
        stack = [(start_x, start_y)]
        contour = []

        while stack:
            x, y = stack.pop()
            if x < 0 or x >= w or y < 0 or y >= h:
                continue
            if visited[y, x] or edges[y, x] == 0:
                continue

            visited[y, x] = True
            contour.append([y, x])

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                stack.append((x + dx, y + dy))

        return np.array(contour) if contour else np.array([])

    def _contour_area(self, contour: np.ndarray) -> float:
        if len(contour) < 3:
            return 0.0
        try:
            min_y, min_x = contour.min(axis=0)
            max_y, max_x = contour.max(axis=0)
            return float((max_x - min_x) * (max_y - min_y))
        except Exception:
            return float(len(contour))

    def _bounding_box(self, contour: np.ndarray) -> Tuple[int, int, int, int]:
        min_y, min_x = contour.min(axis=0)
        max_y, max_x = contour.max(axis=0)
        return (int(min_x), int(min_y), int(max_x), int(max_y))

    def _estimate_scales_from_camera_distances(
        self,
        images: Dict[WalnutSideEnum, Image.Image],
        pixel_dimensions: Dict[str, float],
        camera_distances: Dict[WalnutSideEnum, float],
    ) -> Dict[str, float]:
        focal_length_px = 1000.0

        front_distance = camera_distances[WalnutSideEnum.FRONT]
        back_distance = camera_distances[WalnutSideEnum.BACK]
        left_distance = camera_distances[WalnutSideEnum.LEFT]
        right_distance = camera_distances[WalnutSideEnum.RIGHT]
        top_distance = camera_distances[WalnutSideEnum.TOP]
        down_distance = camera_distances[WalnutSideEnum.DOWN]

        length_px = pixel_dimensions["length"]
        width_px = pixel_dimensions["width"]
        height_px = pixel_dimensions["height"]

        if length_px > 0:
            front_scale = (front_distance / focal_length_px) if front_distance > 0 else (self.default_walnut_size_mm / length_px)
            back_scale = (back_distance / focal_length_px) if back_distance > 0 else (self.default_walnut_size_mm / length_px)
            length_scale = (front_scale + back_scale) / 2.0
        else:
            length_scale = self.default_walnut_size_mm / max(images[WalnutSideEnum.FRONT].size[0], images[WalnutSideEnum.BACK].size[0])

        if width_px > 0:
            left_scale = (left_distance / focal_length_px) if left_distance > 0 else (self.default_walnut_size_mm / width_px)
            right_scale = (right_distance / focal_length_px) if right_distance > 0 else (self.default_walnut_size_mm / width_px)
            width_scale = (left_scale + right_scale) / 2.0
        else:
            width_scale = self.default_walnut_size_mm / max(images[WalnutSideEnum.LEFT].size[0], images[WalnutSideEnum.RIGHT].size[0])

        if height_px > 0:
            top_scale = (top_distance / focal_length_px) if top_distance > 0 else (self.default_walnut_size_mm / height_px)
            down_scale = (down_distance / focal_length_px) if down_distance > 0 else (self.default_walnut_size_mm / height_px)
            height_scale = (top_scale + down_scale) / 2.0
        else:
            height_scale = self.default_walnut_size_mm / max(images[WalnutSideEnum.TOP].size[1], images[WalnutSideEnum.DOWN].size[1])

        return {"length": length_scale, "width": width_scale, "height": height_scale}

    def _save_intermediate_image(
        self, image_array: np.ndarray, image_vo: ImageValueObject, step_name: str
    ) -> None:
        """Save an intermediate grayscale or edge detection image."""
        if image_array.ndim == 2:
            img = Image.fromarray(image_array, mode="L")
        else:
            img = Image.fromarray(image_array)

        output_path = self._get_intermediate_path(image_vo, step_name)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path)

    def _save_intermediate_contour(
        self,
        original_image: np.ndarray,
        all_contours: list[np.ndarray],
        largest_contour: np.ndarray,
        image_vo: ImageValueObject,
        step_name: str,
    ) -> None:
        """Save an intermediate image showing all contours and highlighting the largest one."""
        if original_image.ndim == 3:
            img = Image.fromarray(original_image)
        else:
            img = Image.fromarray(original_image, mode="L").convert("RGB")

        draw = ImageDraw.Draw(img)

        for contour in all_contours:
            if len(contour) > 0:
                points = [(int(pt[1]), int(pt[0])) for pt in contour]
                if len(points) > 2:
                    draw.polygon(points, outline="blue", width=1)

        if len(largest_contour) > 0:
            points = [(int(pt[1]), int(pt[0])) for pt in largest_contour]
            if len(points) > 2:
                draw.polygon(points, outline="red", width=3)

        output_path = self._get_intermediate_path(image_vo, step_name)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path)

    def _save_intermediate_bbox(
        self, original_image: np.ndarray, bbox: Tuple[int, int, int, int], image_vo: ImageValueObject, step_name: str
    ) -> None:
        """Save an intermediate image showing the bounding box."""
        if original_image.ndim == 3:
            img = Image.fromarray(original_image)
        else:
            img = Image.fromarray(original_image, mode="L").convert("RGB")

        draw = ImageDraw.Draw(img)
        draw.rectangle(bbox, outline="green", width=3)

        center_x = original_image.shape[1] // 2
        center_y = original_image.shape[0] // 2
        bbox_center_x = (bbox[0] + bbox[2]) // 2
        bbox_center_y = (bbox[1] + bbox[3]) // 2

        draw.ellipse(
            [center_x - 5, center_y - 5, center_x + 5, center_y + 5], fill="yellow", outline="yellow"
        )
        draw.ellipse(
            [bbox_center_x - 5, bbox_center_y - 5, bbox_center_x + 5, bbox_center_y + 5],
            fill="red",
            outline="red",
        )

        output_path = self._get_intermediate_path(image_vo, step_name)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path)

    def _get_intermediate_path(self, image_vo: ImageValueObject, step_name: str) -> Path:
        """Generate the path for an intermediate result file."""
        original_path = Path(image_vo.path)
        side_name = image_vo.side.value.lower()
        intermediate_dir = original_path.parent / "_intermediate"
        stem = original_path.stem
        suffix = original_path.suffix
        filename = f"{stem}_intermediate_{step_name}_{side_name}{suffix}"
        return intermediate_dir / filename

