# infrastructure_layer/services/image_object__finder.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np


# =========================
# Constants
# =========================

# Brown color detection in HSV
BROWN_HUE_MIN = 0
BROWN_HUE_MAX = 30
BROWN_HUE_WRAP_MIN = 170  # Red-brown wraps around at 180
BROWN_HUE_WRAP_MAX = 179
BROWN_SAT_MIN = 50
BROWN_VAL_MIN = 50
BROWN_VAL_MAX = 200

# Image processing parameters
BLUR_DIAMETER = 9
BLUR_SIGMA_COLOR = 75
BLUR_SIGMA_SPACE = 75
THRESHOLD_BLOCK_SIZE = 31
THRESHOLD_C = 5
MORPH_KERNEL_SIZE = 5
CANNY_LOW_THRESHOLD = 50
CANNY_HIGH_THRESHOLD = 150

# Object filtering thresholds
MIN_AREA_FOR_DETECTION = 500
MIN_AREA_FOR_CANDIDATE = 1000
MIN_BROWN_SCORE = 0.3
MAX_CIRCULARITY_FOR_PILLARS = 0.95
BORDER_MARGIN = 10

# Scoring weights
SCORE_BROWN_WEIGHT = 0.4
SCORE_AREA_WEIGHT = 0.25
SCORE_CIRCULARITY_WEIGHT = 0.2
SCORE_TEXTURE_WEIGHT = 0.15

# Normalization factors
MAX_TEXTURE_SCORE = 10000.0
MAX_AREA_SCORE = 500000.0
IDEAL_CIRCULARITY_MIN = 0.7
IDEAL_CIRCULARITY_MAX = 0.9
CIRCULARITY_PENALTY_FACTOR = 0.5


# =========================
# Data Structures
# =========================

@dataclass
class ObjectDetectionResult:
    """Result of object detection in an image."""
    contour: np.ndarray
    area: float
    width_px: float
    height_px: float
    center_x: float
    center_y: float


@dataclass
class DetectedObject:
    """Extended result with additional features for filtering and scoring."""
    contour: np.ndarray
    area: float
    width_px: float
    height_px: float
    center_x: float
    center_y: float
    aspect_ratio: float
    circularity: float
    texture_score: float
    brown_score: float


# =========================
# Interface
# =========================

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
            intermediate_dir: Optional directory path to save intermediate images
        
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


# =========================
# Implementation
# =========================

class ImageObjectFinder(IImageObjectFinder):
    """
    Object finder that identifies brown objects (walnuts) in images.
    
    Processing pipeline:
    1. Create brown color mask
    2. Apply mask to image (self-bounded processing)
    3. Grayscale conversion
    4. Blur
    5. Threshold
    6. Morphological cleanup
    7. Edge detection
    8. Contour finding
    9. Feature extraction and scoring
    """

    def find_object(
        self,
        image_path: str,
        background_is_white: bool = True,
        intermediate_dir: Optional[str] = None,
    ) -> Optional[ObjectDetectionResult]:
        """
        Find the walnut in an image.
        
        Filters out:
        - Objects touching borders (glass box edges)
        - Perfect circles (pillars)
        - Very small objects
        - Non-brown objects
        
        Returns the best candidate based on scoring.
        """
        # Load image to get dimensions for border checking
        image = cv2.imread(image_path)
        if image is None:
            return None
        image_height, image_width = image.shape[:2]
        
        # Detect all objects with detailed features
        # Save intermediate files but not objects yet (we'll save objects after determining match)
        all_objects = self._find_all_objects_detailed(
            image_path=image_path,
            background_is_white=background_is_white,
            intermediate_dir=intermediate_dir,  # Save intermediate processing files
            min_area=MIN_AREA_FOR_DETECTION,
            matched_object=None,  # Don't save objects yet
            save_objects=False,  # Skip object saving for now
        )
        if not all_objects:
            return None
        
        # Filter and score candidates
        candidates = self._filter_and_score_candidates(
            all_objects, image_width, image_height
        )
        
        # Determine matched object
        if not candidates:
            # Fallback: use largest object if no candidates pass filters
            matched_obj = max(all_objects, key=lambda o: o.area)
        else:
            # Use best candidate (highest score)
            matched_obj = max(candidates, key=lambda x: x[1])[0]
        
        # Now save all objects with match indicator
        if intermediate_dir:
            image = cv2.imread(image_path)
            if image is not None:
                self._save_all_objects_with_scores(
                    image, all_objects, matched_obj, intermediate_dir, image_path
                )
        
        return self._convert_to_result(matched_obj)

    def find_all_objects(
        self,
        image_path: str,
        background_is_white: bool = True,
        min_contour_size: int = 10,
    ) -> List[ObjectDetectionResult]:
        """Find all objects/components in an image."""
        detected_objects = self._find_all_objects_detailed(
            image_path=image_path,
            intermediate_dir=None,
            background_is_white=background_is_white,
            min_area=min_contour_size,
        )
        
        return [self._convert_to_result(obj) for obj in detected_objects]

    # =========================
    # Main Processing Pipeline
    # =========================

    def _find_all_objects_detailed(
        self,
        image_path: str,
        intermediate_dir: Optional[str],
        background_is_white: bool = True,
        min_area: int = 300,
        matched_object: Optional[DetectedObject] = None,
        save_objects: bool = True,
    ) -> List[DetectedObject]:
        """
        Main processing pipeline to detect objects.
        
        Steps:
        1. Load image and convert to HSV
        2. Create brown mask
        3. Apply mask (self-bounded)
        4. Grayscale
        5. Blur
        6. Threshold
        7. Morphological cleanup
        8. Edge detection
        9. Find contours
        10. Extract features
        """
        # Load image first to get name for directory structure
        image = self._load_image(image_path)
        out_dir = self._setup_output_directory(intermediate_dir, image_path)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Create brown mask and apply to image
        brown_mask = self._create_brown_mask(hsv)
        self._save_intermediate(out_dir, "00_brown_mask.png", brown_mask * 255)
        
        masked_image = cv2.bitwise_and(image, image, mask=brown_mask)
        self._save_intermediate(out_dir, "01_masked_image.png", masked_image)
        
        # Image processing pipeline
        gray = cv2.cvtColor(masked_image, cv2.COLOR_BGR2GRAY)
        self._save_intermediate(out_dir, "02_gray.png", gray)
        
        blur = cv2.bilateralFilter(
            gray, BLUR_DIAMETER, BLUR_SIGMA_COLOR, BLUR_SIGMA_SPACE
        )
        self._save_intermediate(out_dir, "03_blur.png", blur)
        
        thresh = self._adaptive_threshold(blur, background_is_white)
        self._save_intermediate(out_dir, "04_threshold.png", thresh)
        
        cleaned = self._morphological_cleanup(thresh)
        self._save_intermediate(out_dir, "05_cleaned.png", cleaned)
        
        edges = cv2.Canny(gray, CANNY_LOW_THRESHOLD, CANNY_HIGH_THRESHOLD)
        self._save_intermediate(out_dir, "06_edges.png", edges)
        
        # Find and analyze contours
        contours, _ = cv2.findContours(
            cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        objects = self._extract_objects_from_contours(
            contours, gray, edges, hsv, image, min_area, out_dir, matched_object, save_objects
        )
        
        # Save final overlay
        if out_dir:
            overlay = image.copy()
            cv2.drawContours(overlay, [o.contour for o in objects], -1, (0, 0, 255), 2)
            cv2.imwrite(str(out_dir / "07_all_contours.png"), overlay)
        
        return sorted(objects, key=lambda o: o.area, reverse=True)

    # =========================
    # Image Processing Helpers
    # =========================

    def _load_image(self, image_path: str) -> np.ndarray:
        """Load image from file."""
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Cannot read image: {image_path}")
        return image

    def _setup_output_directory(
        self, intermediate_dir: Optional[str], image_path: str
    ) -> Optional[Path]:
        """
        Setup output directory for intermediate files.
        
        Structure: {intermediate_dir}/{image_name}/
        Example: _intermediate/00001_T/
        """
        if intermediate_dir:
            # Get image name without extension (e.g., "00001_T" from "00001_T.jpg")
            image_path_obj = Path(image_path)
            image_name = image_path_obj.stem
            
            # Create nested directory: {intermediate_dir}/{image_name}/
            out_dir = Path(intermediate_dir) / image_name
            out_dir.mkdir(parents=True, exist_ok=True)
            return out_dir
        return None

    def _save_intermediate(self, out_dir: Optional[Path], filename: str, image: np.ndarray) -> None:
        """Save intermediate processing result."""
        if out_dir:
            cv2.imwrite(str(out_dir / filename), image)

    def _adaptive_threshold(
        self, blur: np.ndarray, background_is_white: bool
    ) -> np.ndarray:
        """Apply adaptive thresholding."""
        threshold_type = (
            cv2.THRESH_BINARY_INV if background_is_white else cv2.THRESH_BINARY
        )
        return cv2.adaptiveThreshold(
            blur,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            threshold_type,
            THRESHOLD_BLOCK_SIZE,
            THRESHOLD_C,
        )

    def _morphological_cleanup(self, thresh: np.ndarray) -> np.ndarray:
        """Apply morphological operations to clean up threshold result."""
        kernel = np.ones((MORPH_KERNEL_SIZE, MORPH_KERNEL_SIZE), np.uint8)
        return cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # =========================
    # Color Detection
    # =========================

    def _create_brown_mask(self, hsv: np.ndarray) -> np.ndarray:
        """
        Create a mask highlighting brown objects in the image.
        
        Brown color range in HSV:
        - Hue: 0-30 (red-brown to orange-brown) or 170-179 (wraps around)
        - Saturation: 50-255 (moderate to high)
        - Value: 50-200 (moderate brightness)
        
        Returns:
            Binary mask (0 or 255) where 255 indicates brown pixels
        """
        h = hsv[:, :, 0]  # Hue (0-179 in OpenCV)
        s = hsv[:, :, 1]  # Saturation (0-255)
        v = hsv[:, :, 2]  # Value/Brightness (0-255)
        
        # Brown hue range (including wrap-around)
        brown_hue = (
            ((h >= BROWN_HUE_MIN) & (h <= BROWN_HUE_MAX)) |
            ((h >= BROWN_HUE_WRAP_MIN) & (h <= BROWN_HUE_WRAP_MAX))
        )
        
        # Combined brown mask
        brown_mask = (
            brown_hue &
            (s >= BROWN_SAT_MIN) &
            (v >= BROWN_VAL_MIN) &
            (v <= BROWN_VAL_MAX)
        )
        
        return brown_mask.astype(np.uint8)

    def _brown_score(self, contour: np.ndarray, hsv: np.ndarray) -> float:
        """
        Calculate how brown an object is (0-1).
        
        Returns the ratio of brown pixels within the contour region.
        """
        # Create mask for the contour region
        mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        cv2.drawContours(mask, [contour], -1, 255, -1)
        
        # Get HSV values within the contour
        hsv_roi = hsv[mask == 255]
        if len(hsv_roi) == 0:
            return 0.0
        
        # Extract channels
        h_values = hsv_roi[:, 0]
        s_values = hsv_roi[:, 1]
        v_values = hsv_roi[:, 2]
        
        # Brown color detection (same logic as mask creation)
        brown_hue = (
            ((h_values >= BROWN_HUE_MIN) & (h_values <= BROWN_HUE_MAX)) |
            ((h_values >= BROWN_HUE_WRAP_MIN) & (h_values <= BROWN_HUE_WRAP_MAX))
        )
        brown_mask = (
            brown_hue &
            (s_values >= BROWN_SAT_MIN) &
            (v_values >= BROWN_VAL_MIN) &
            (v_values <= BROWN_VAL_MAX)
        )
        
        brown_pixel_count = np.sum(brown_mask)
        total_pixel_count = len(hsv_roi)
        
        return float(brown_pixel_count) / float(total_pixel_count) if total_pixel_count > 0 else 0.0

    # =========================
    # Feature Extraction
    # =========================

    def _extract_objects_from_contours(
        self,
        contours: List[np.ndarray],
        gray: np.ndarray,
        edges: np.ndarray,
        hsv: np.ndarray,
        image: np.ndarray,
        min_area: int,
        out_dir: Optional[Path],
        matched_object: Optional[DetectedObject],
        save_objects: bool = True,
    ) -> List[DetectedObject]:
        """Extract DetectedObject from contours."""
        objects = []
        
        for idx, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area < min_area:
                continue
            
            obj = self._analyze_contour(contour, gray, edges, hsv, image)
            objects.append(obj)
            
            # Save per-object visualization with scores (if enabled)
            if save_objects and out_dir:
                is_match = matched_object is not None and self._is_same_object(obj, matched_object)
                self._save_object_debug(image, obj, idx, out_dir, is_match)
        
        return objects

    def _analyze_contour(
        self,
        contour: np.ndarray,
        gray: np.ndarray,
        edges: np.ndarray,
        hsv: np.ndarray,
        image: np.ndarray,
    ) -> DetectedObject:
        """Extract all features from a contour."""
        x, y, w, h = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)
        center_x = x + w / 2
        center_y = y + h / 2
        aspect_ratio = w / h if h > 0 else 0.0
        
        perimeter = cv2.arcLength(contour, True)
        circularity = (
            4 * np.pi * area / (perimeter ** 2) if perimeter > 0 else 0.0
        )
        
        texture_score = self._texture_score(contour, edges)
        brown_score = self._brown_score(contour, hsv)
        
        return DetectedObject(
            contour=contour,
            area=float(area),
            width_px=float(w),
            height_px=float(h),
            center_x=float(center_x),
            center_y=float(center_y),
            aspect_ratio=float(aspect_ratio),
            circularity=float(circularity),
            texture_score=float(texture_score),
            brown_score=float(brown_score),
        )

    def _texture_score(self, contour: np.ndarray, edges: np.ndarray) -> float:
        """
        Measure how textured an object is.
        
        Returns the number of edge pixels within the contour region.
        Walnuts have high texture (many edges), glass box has low texture.
        """
        mask = np.zeros(edges.shape, dtype=np.uint8)
        cv2.drawContours(mask, [contour], -1, 255, -1)
        edge_pixels = edges[mask == 255]
        return float(len(edge_pixels))

    # =========================
    # Filtering and Scoring
    # =========================

    def _filter_and_score_candidates(
        self,
        all_objects: List[DetectedObject],
        image_width: int,
        image_height: int,
    ) -> List[tuple[DetectedObject, float]]:
        """
        Filter objects and calculate scores.
        
        Returns list of (object, score) tuples for candidates that pass all filters.
        """
        candidates = []
        
        for obj in all_objects:
            # Apply filters
            if self._should_filter_out(obj, image_width, image_height):
                continue
            
            # Calculate score
            score = self._calculate_score(obj)
            candidates.append((obj, score))
        
        return candidates

    def _should_filter_out(
        self,
        obj: DetectedObject,
        image_width: int,
        image_height: int,
    ) -> bool:
        """Check if object should be filtered out."""
        # Filter out objects touching borders
        if self._touches_border(obj, image_width, image_height):
            return True
        
        # Filter out perfect circles (pillars)
        if obj.circularity > MAX_CIRCULARITY_FOR_PILLARS:
            return True
        
        # Filter out very small objects
        if obj.area < MIN_AREA_FOR_CANDIDATE:
            return True
        
        # Filter out non-brown objects
        if obj.brown_score < MIN_BROWN_SCORE:
            return True
        
        return False

    def _calculate_score(self, obj: DetectedObject) -> float:
        """
        Calculate composite score for object.
        
        Higher score = better candidate for walnut.
        Combines brown color, area, circularity, and texture.
        """
        # Normalize features to 0-1 range
        normalized_texture = min(obj.texture_score / MAX_TEXTURE_SCORE, 1.0)
        normalized_area = min(obj.area / MAX_AREA_SCORE, 1.0)
        
        # Prefer circularity in ideal range (walnut is close to circle but not perfect)
        if IDEAL_CIRCULARITY_MIN <= obj.circularity <= IDEAL_CIRCULARITY_MAX:
            circularity_score = obj.circularity
        else:
            circularity_score = obj.circularity * CIRCULARITY_PENALTY_FACTOR
        
        # Weighted combination
        score = (
            SCORE_BROWN_WEIGHT * obj.brown_score +
            SCORE_AREA_WEIGHT * normalized_area +
            SCORE_CIRCULARITY_WEIGHT * circularity_score +
            SCORE_TEXTURE_WEIGHT * normalized_texture
        )
        
        return score

    def _touches_border(
        self,
        obj: DetectedObject,
        image_width: int,
        image_height: int,
    ) -> bool:
        """
        Check if object contour touches image borders.
        
        Glass box edges typically touch borders, walnuts don't.
        """
        # Check contour points
        contour_points = obj.contour.reshape(-1, 2)
        for point in contour_points:
            px, py = point[0], point[1]  # (x, y) format from cv2
            if (
                px <= BORDER_MARGIN or px >= (image_width - BORDER_MARGIN) or
                py <= BORDER_MARGIN or py >= (image_height - BORDER_MARGIN)
            ):
                return True
        
        # Check bounding box center
        if (
            obj.center_x <= BORDER_MARGIN or
            obj.center_x >= (image_width - BORDER_MARGIN) or
            obj.center_y <= BORDER_MARGIN or
            obj.center_y >= (image_height - BORDER_MARGIN)
        ):
            return True
        
        return False

    def _convert_to_result(self, obj: DetectedObject) -> ObjectDetectionResult:
        """Convert DetectedObject to ObjectDetectionResult."""
        return ObjectDetectionResult(
            contour=obj.contour,
            area=obj.area,
            width_px=obj.width_px,
            height_px=obj.height_px,
            center_x=obj.center_x,
            center_y=obj.center_y,
        )

    # =========================
    # Debug Helpers
    # =========================

    def _save_object_debug(
        self,
        image: np.ndarray,
        obj: DetectedObject,
        index: int,
        out_dir: Path,
        is_match: bool = False,
    ) -> None:
        """
        Save debug visualization for a single object with scores in filename.
        
        Filename format: object_{index:02d}_brownscore_{brown:.2f}_texturescore_{texture:.1f}_circularity_{circ:.2f}_area_{area:.0f}{_match}.png
        """
        debug_img = image.copy()
        cv2.drawContours(debug_img, [obj.contour], -1, (0, 255, 0), 2)
        
        x, y, w, h = cv2.boundingRect(obj.contour)
        cv2.rectangle(debug_img, (x, y), (x + w, y + h), (255, 0, 0), 2)
        
        # Build filename with scores
        filename = (
            f"object_{index:02d}_"
            f"brownscore_{obj.brown_score:.2f}_"
            f"texturescore_{obj.texture_score:.1f}_"
            f"circularity_{obj.circularity:.2f}_"
            f"area_{obj.area:.0f}"
        )
        if is_match:
            filename += "_match"
        filename += ".png"
        
        cv2.imwrite(str(out_dir / filename), debug_img)

    def _save_all_objects_with_scores(
        self,
        image: np.ndarray,
        all_objects: List[DetectedObject],
        matched_obj: DetectedObject,
        intermediate_dir: str,
        image_path: str,
    ) -> None:
        """Save all objects with scores, marking the matched one."""
        # Get output directory
        image_path_obj = Path(image_path)
        image_name = image_path_obj.stem
        out_dir = Path(intermediate_dir) / image_name
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # Save all objects
        for idx, obj in enumerate(all_objects):
            is_match = self._is_same_object(obj, matched_obj)
            self._save_object_debug(image, obj, idx, out_dir, is_match)

    def _is_same_object(self, obj1: DetectedObject, obj2: DetectedObject) -> bool:
        """Check if two objects are the same (by comparing contour area and center)."""
        # Compare by area and center position (with small tolerance)
        area_diff = abs(obj1.area - obj2.area) / max(obj1.area, obj2.area, 1.0)
        center_diff = (
            abs(obj1.center_x - obj2.center_x) + abs(obj1.center_y - obj2.center_y)
        )
        
        # Same object if area is very similar and centers are close
        return area_diff < 0.01 and center_diff < 5.0


# =========================
# Example Usage
# =========================

if __name__ == "__main__":
    finder = ImageObjectFinder()
    
    results = finder._find_all_objects_detailed(
        image_path="walnut.jpg",
        intermediate_dir="debug_output",
        background_is_white=True,
    )
    
    for i, r in enumerate(results):
        print(
            f"[{i}] area={r.area:.0f}, "
            f"circularity={r.circularity:.2f}, "
            f"texture={r.texture_score:.0f}, "
            f"brown={r.brown_score:.2f}"
        )
