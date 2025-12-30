# infrastructure_layer/services/walnut_image_service/image_segmenter.py
from typing import Optional

import numpy as np


class ImageSegmenter:
    """Handles image segmentation to extract walnut silhouette."""

    def __init__(self, background_is_white: bool = True) -> None:
        self.background_is_white: bool = background_is_white

    def segment_walnut(self, gray: np.ndarray) -> Optional[np.ndarray]:
        """
        Segment walnut from background using OTSU thresholding.
        Returns binary mask where 255 = walnut, 0 = background.
        """
        # Apply OTSU thresholding for automatic threshold selection
        threshold_value = self._otsu_threshold(gray)
        
        # Create binary mask
        if self.background_is_white:
            # Background is white, walnut is darker - invert
            mask = (gray < threshold_value).astype(np.uint8) * 255
        else:
            # Background is dark, walnut is lighter
            mask = (gray > threshold_value).astype(np.uint8) * 255
        
        return mask

    def _otsu_threshold(self, gray: np.ndarray) -> float:
        """
        Calculate OTSU threshold for binary segmentation.
        OTSU automatically finds the optimal threshold value.
        """
        hist, bin_edges = np.histogram(gray.flatten(), bins=256, range=(0, 256))
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0
        
        # Normalize histogram
        hist = hist.astype(np.float32)
        hist /= hist.sum()
        
        # Calculate between-class variance for each threshold
        best_threshold = 0
        max_variance = 0.0
        
        for threshold in range(1, 256):
            # Split histogram at threshold
            w0 = hist[:threshold].sum()
            w1 = hist[threshold:].sum()
            
            if w0 == 0 or w1 == 0:
                continue
            
            # Mean values for each class
            m0 = (bin_centers[:threshold] * hist[:threshold]).sum() / w0
            m1 = (bin_centers[threshold:] * hist[threshold:]).sum() / w1
            
            # Between-class variance
            variance = w0 * w1 * (m0 - m1) ** 2
            
            if variance > max_variance:
                max_variance = variance
                best_threshold = threshold
        
        return float(best_threshold)

