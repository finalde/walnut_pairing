from dataclasses import dataclass
from pathlib import Path
from typing import List

import cv2
import numpy as np


# =========================
# Data structure
# =========================

@dataclass
class DetectedObject:
    contour: np.ndarray
    area: float
    width_px: float
    height_px: float
    center_x: float
    center_y: float
    aspect_ratio: float
    circularity: float
    texture_score: float


# =========================
# Main finder
# =========================

class WalnutObjectFinder:
    """
    Simple, debuggable object finder.
    Finds ALL objects, computes shape + texture features,
    and saves ALL intermediate results.
    """

    def find_all_objects(
        self,
        image_path: str,
        intermediate_dir: str,
        background_is_white: bool = True,
        min_area: int = 300,
    ) -> List[DetectedObject]:

        out_dir = Path(intermediate_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Load
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Cannot read image: {image_path}")

        # 2. Grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(str(out_dir / "01_gray.png"), gray)

        # 3. Edge-preserving blur (keeps walnut texture)
        blur = cv2.bilateralFilter(gray, 9, 75, 75)
        cv2.imwrite(str(out_dir / "02_blur.png"), blur)

        # 4. Adaptive threshold (plate-safe)
        thresh = cv2.adaptiveThreshold(
            blur,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV if background_is_white else cv2.THRESH_BINARY,
            blockSize=31,
            C=5,
        )
        cv2.imwrite(str(out_dir / "03_threshold.png"), thresh)

        # 5. Morphological cleanup
        kernel = np.ones((5, 5), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        cv2.imwrite(str(out_dir / "04_cleaned.png"), cleaned)

        # 6. Edge map (texture inspection)
        edges = cv2.Canny(gray, 50, 150)
        cv2.imwrite(str(out_dir / "05_edges.png"), edges)

        # 7. Find contours
        contours, _ = cv2.findContours(
            cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        objects: List[DetectedObject] = []

        for idx, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area < min_area:
                continue

            obj = self._analyze_contour(contour, gray, edges)
            objects.append(obj)

            # Save per-object visualization
            self._save_object_debug(
                image=image,
                contour=contour,
                index=idx,
                out_dir=out_dir,
            )

        # 8. Save all contours overlay
        overlay = image.copy()
        cv2.drawContours(overlay, [o.contour for o in objects], -1, (0, 0, 255), 2)
        cv2.imwrite(str(out_dir / "06_all_contours.png"), overlay)

        # Sort by area (largest first)
        return sorted(objects, key=lambda o: o.area, reverse=True)

    # =========================
    # Feature extraction
    # =========================

    def _analyze_contour(
        self,
        contour: np.ndarray,
        gray: np.ndarray,
        edges: np.ndarray,
    ) -> DetectedObject:

        x, y, w, h = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)

        center_x = x + w / 2
        center_y = y + h / 2

        aspect_ratio = w / h if h > 0 else 0.0

        perimeter = cv2.arcLength(contour, True)
        circularity = (
            4 * np.pi * area / (perimeter ** 2)
            if perimeter > 0 else 0.0
        )

        texture_score = self._texture_score(contour, edges)

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
        )

    def _texture_score(
        self,
        contour: np.ndarray,
        edges: np.ndarray,
    ) -> float:
        """
        Measures how textured an object is.
        Plate → low edges
        Walnut → high edges
        """
        mask = np.zeros(edges.shape, dtype=np.uint8)
        cv2.drawContours(mask, [contour], -1, 255, -1)

        edge_pixels = edges[mask == 255]
        return float(len(edge_pixels))

    # =========================
    # Debug helpers
    # =========================

    def _save_object_debug(
        self,
        image: np.ndarray,
        contour: np.ndarray,
        index: int,
        out_dir: Path,
    ) -> None:

        debug_img = image.copy()
        cv2.drawContours(debug_img, [contour], -1, (0, 255, 0), 2)

        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(debug_img, (x, y), (x + w, y + h), (255, 0, 0), 2)

        cv2.imwrite(
            str(out_dir / f"object_{index:02d}.png"),
            debug_img,
        )


# =========================
# Example usage
# =========================

if __name__ == "__main__":
    finder = WalnutObjectFinder()

    results = finder.find_all_objects(
        image_path="walnut.jpg",
        intermediate_dir="debug_output",
        background_is_white=True,
    )

    for i, r in enumerate(results):
        print(
            f"[{i}] area={r.area:.0f}, "
            f"circularity={r.circularity:.2f}, "
            f"texture={r.texture_score:.0f}, "
            f"aspect_ratio={r.aspect_ratio:.2f}"
        )
