# infrastructure_layer/file_readers/walnut_image__file_reader.py
"""File reader to load walnut images from filesystem and create file DAOs."""
import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from common.enums import WalnutSideEnum
from common.logger import get_logger
from infrastructure_layer.data_access_objects.walnut__file_dao import WalnutFileDAO, WalnutImageFileDAO
from PIL import Image


class IWalnutImageFileReader(ABC):
    """Interface for reading walnut image data from filesystem."""

    @abstractmethod
    def load_walnut_from_directory(self, walnut_id: str, image_directory: Path) -> Optional[WalnutFileDAO]:
        """
        Load a walnut's images from a directory and create a file DAO.

        Args:
            walnut_id: The ID of the walnut (e.g., "0001")
            image_directory: Path to the directory containing images

        Returns:
            WalnutFileDAO with all images loaded, or None if directory doesn't exist
        """
        pass


class WalnutImageFileReader(IWalnutImageFileReader):
    """Loads walnut images from filesystem and creates file DAOs."""

    # Mapping from side enum to file name letter
    SIDE_TO_LETTER = {
        WalnutSideEnum.FRONT: "F",
        WalnutSideEnum.BACK: "B",
        WalnutSideEnum.LEFT: "L",
        WalnutSideEnum.RIGHT: "R",
        WalnutSideEnum.TOP: "T",
        WalnutSideEnum.DOWN: "D",
    }

    LETTER_TO_SIDE = {v: k for k, v in SIDE_TO_LETTER.items()}

    def __init__(self) -> None:
        """Initialize the file reader."""
        self.logger = get_logger(__name__)

    @staticmethod
    def _calculate_checksum(file_path: Path) -> str:
        """Calculate MD5 checksum of a file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _parse_filename(self, file_path: Path) -> Optional[str]:
        """
        Parse filename to extract side letter.
        Expected format: {walnut_id}_{SIDE_LETTER}_{number}.jpg
        Example: 0001_F_1.jpg -> "F"
        """
        parts = file_path.stem.split("_")
        if len(parts) >= 2:
            letter = parts[1].upper()
            if letter in self.LETTER_TO_SIDE:
                return letter
        return None

    def load_walnut_from_directory(self, walnut_id: str, image_directory: Path) -> Optional[WalnutFileDAO]:
        """
        Load a walnut's images from a directory and create a file DAO.

        Args:
            walnut_id: The ID of the walnut (e.g., "0001")
            image_directory: Path to the directory containing images

        Returns:
            WalnutFileDAO with all images loaded, or None if directory doesn't exist
        """
        if not image_directory.exists() or not image_directory.is_dir():
            return None

        images: List[WalnutImageFileDAO] = []

        # Look for image files matching the pattern
        for file_path in image_directory.glob(f"{walnut_id}_*.jpg"):
            side_letter = self._parse_filename(file_path)
            if side_letter is None:
                continue

            try:
                # Load image to get dimensions
                with Image.open(file_path) as img:
                    width, height = img.size

                # Get file size
                file_size = file_path.stat().st_size

                # Calculate checksum
                checksum = self._calculate_checksum(file_path)

                image_dao = WalnutImageFileDAO(
                    file_path=file_path,
                    side_letter=side_letter,
                    width=width,
                    height=height,
                    file_size=file_size,
                    checksum=checksum,
                )
                images.append(image_dao)
            except Exception as e:
                self.logger.warning(
                    "image_load_error",
                    file_path=str(file_path),
                    error=str(e),
                )
                continue

        if not images:
            return None

        return WalnutFileDAO(
            walnut_id=walnut_id,
            image_directory=image_directory,
            images=images,
        )
