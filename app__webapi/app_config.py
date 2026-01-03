# app__webapi/app_config.py
"""WebAPI application configuration."""
from pathlib import Path
from typing import Dict, Optional

import yaml
from common.enums import WalnutSideEnum
from common.interfaces import (
    IAppConfig,
    DatabaseConfig,
    CameraConfig,
    AlgorithmConfig,
)


class WebAPIAppConfig(IAppConfig):
    """WebAPI-specific application configuration implementation.
    
    This implementation only includes the database configuration,
    as other properties (image_root, cameras, algorithm) are not
    needed for the web API.
    """

    def __init__(self, database: dict) -> None:
        """
        Initialize WebAPI configuration.

        Args:
            database: Database configuration dictionary
        """
        self._database: DatabaseConfig = DatabaseConfig(**database)
        # Set defaults for properties not used in webapi
        self._image_root: str = ""
        self._cameras: Dict[WalnutSideEnum, CameraConfig] = {}
        self._algorithm: Optional[AlgorithmConfig] = None

    @property
    def image_root(self) -> str:
        """Get the root path for images (not used in webapi)."""
        return self._image_root

    @property
    def database(self) -> DatabaseConfig:
        """Get the database configuration."""
        return self._database

    @property
    def cameras(self) -> Dict[WalnutSideEnum, CameraConfig]:
        """Get camera configurations (not used in webapi, returns empty dict)."""
        return self._cameras

    def get_camera_config(self, side: WalnutSideEnum) -> Optional[CameraConfig]:
        """Get camera configuration for a specific side (not used in webapi)."""
        return None

    @property
    def algorithm(self) -> Optional[AlgorithmConfig]:
        """Get algorithm comparison configuration (not used in webapi)."""
        return self._algorithm

    @classmethod
    def load_from_yaml(cls, yaml_path: Path) -> "WebAPIAppConfig":
        """Load configuration from YAML file."""
        with open(yaml_path, "r") as f:
            cfg = yaml.safe_load(f)
        return cls(database=cfg.get("database", {}))

