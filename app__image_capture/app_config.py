# app__image_capture/app_config.py
"""Image capture application configuration."""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from common.enums import WalnutSideEnum
from common.interfaces import (
    IAppConfig,
    DatabaseConfig,
    CameraConfig,
    AlgorithmConfig,
    CaptureConfig,
    ScanConfig,
    FileNamingConfig,
    CameraRolesConfig,
)


class ImageCaptureAppConfig(IAppConfig):
    """Image capture application configuration."""

    def __init__(
        self,
        image_root: str,
        cameras: Dict[str, any],
        capture: Dict[str, any],
        scan: Dict[str, any],
        file_naming: Dict[str, any],
        database: Optional[Dict[str, any]] = None,
    ) -> None:
        """
        Initialize configuration.
        
        Args:
            image_root: Root directory for images
            cameras: Camera roles configuration
            capture: Capture settings configuration
            scan: Scan settings configuration
            file_naming: File naming configuration
            database: Optional database configuration (for IAppConfig compatibility)
        """
        self._image_root: str = image_root
        self._cameras: CameraRolesConfig = CameraRolesConfig(**cameras)
        self._capture: CaptureConfig = CaptureConfig(**capture)
        self._scan: ScanConfig = ScanConfig(**scan)
        self._file_naming: FileNamingConfig = FileNamingConfig(**file_naming)
        
        # Database config (minimal, for IAppConfig compatibility)
        if database:
            self._database: DatabaseConfig = DatabaseConfig(**database)
        else:
            # Create minimal database config
            self._database: DatabaseConfig = DatabaseConfig(
                host="localhost",
                port=5432,
                database="walnut_pairing",
                user="postgres",
                password="",
            )
        
        # For IAppConfig compatibility - cameras as Dict[WalnutSideEnum, CameraConfig]
        # Image capture app doesn't use these, so return empty dict
        self._cameras_dict: Dict[WalnutSideEnum, CameraConfig] = {}
        
        # Algorithm config (not used in image capture app)
        self._algorithm: Optional[AlgorithmConfig] = None

    @property
    def image_root(self) -> str:
        """Get the root path for images."""
        return self._image_root

    @property
    def database(self) -> DatabaseConfig:
        """Get the database configuration."""
        return self._database

    @property
    def cameras(self) -> Dict[WalnutSideEnum, CameraConfig]:
        """Get camera configurations by side (IAppConfig interface - returns empty dict for image capture app)."""
        return self._cameras_dict

    def get_camera_config(self, side: WalnutSideEnum) -> Optional[CameraConfig]:
        """Get camera configuration for a specific side (IAppConfig interface - not used in image capture app)."""
        return None

    @property
    def algorithm(self) -> Optional[AlgorithmConfig]:
        """Get algorithm comparison configuration (IAppConfig interface - not used in image capture app)."""
        return self._algorithm

    @property
    def camera_roles(self) -> CameraRolesConfig:
        """Get camera roles configuration (image capture app specific)."""
        return self._cameras

    @property
    def capture(self) -> CaptureConfig:
        """Get capture configuration (image capture app specific)."""
        return self._capture

    @property
    def scan(self) -> ScanConfig:
        """Get scan configuration (image capture app specific)."""
        return self._scan

    @property
    def file_naming(self) -> FileNamingConfig:
        """Get file naming configuration (image capture app specific)."""
        return self._file_naming

    @classmethod
    def load_from_yaml(cls, yaml_path: Path) -> "ImageCaptureAppConfig":
        """Load configuration from YAML file."""
        with open(yaml_path, "r") as f:
            cfg = yaml.safe_load(f)
        return cls(**cfg)

