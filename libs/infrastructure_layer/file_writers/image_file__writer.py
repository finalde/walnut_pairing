# infrastructure_layer/file_writers/image_file__writer.py
"""File writer for saving images to filesystem."""
import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

import cv2
import numpy as np

from common.logger import get_logger


class IImageFileWriter(ABC):
    """Interface for writing image files to filesystem."""

    @abstractmethod
    async def ensure_directories_async(self, roles: List[str], base_path: str) -> None:
        """
        Ensure directories exist for all roles.
        
        Args:
            roles: List of role names (e.g., ["Front", "Back"])
            base_path: Base directory path for images
        """
        pass

    @abstractmethod
    async def save_image_async(self, image: np.ndarray, path: str) -> bool:
        """
        Save an image to the specified path.
        
        Args:
            image: Image data as numpy array (BGR format from OpenCV)
            path: Full path where image should be saved
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def build_image_path(self, base_path: str, role: str, capture_id: str, suffix: str) -> str:
        """
        Build the full path for an image file.
        
        Args:
            base_path: Base directory path for images
            role: Role name (e.g., "Front")
            capture_id: Capture ID (e.g., "0001")
            suffix: Role suffix (e.g., "F")
            
        Returns:
            Full path string (e.g., "images/Front/0001_F.jpg")
        """
        pass


class ImageFileWriter(IImageFileWriter):
    """Implementation of image file writer."""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    async def ensure_directories_async(self, roles: List[str], base_path: str) -> None:
        """Ensure directories exist for all roles."""
        base = Path(base_path)
        for role in roles:
            role_dir = base / role
            # Run in thread pool since Path.mkdir is blocking
            await asyncio.to_thread(role_dir.mkdir, parents=True, exist_ok=True)

    async def save_image_async(self, image: np.ndarray, path: str) -> bool:
        """Save an image to the specified path."""
        try:
            # Run cv2.imwrite in thread pool since it's blocking
            success = await asyncio.to_thread(cv2.imwrite, path, image)
            if success:
                self.logger.info(f"Saved image to {path}")
            else:
                self.logger.error(f"Failed to save image to {path}")
            return success
        except Exception as e:
            self.logger.error(f"Error saving image to {path}: {e}")
            return False

    def build_image_path(self, base_path: str, role: str, capture_id: str, suffix: str) -> str:
        """Build the full path for an image file."""
        base = Path(base_path)
        role_dir = base / role
        filename = f"{capture_id}_{suffix}.jpg"
        return str(role_dir / filename)

