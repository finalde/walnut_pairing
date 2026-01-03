# batch/app_config.py
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import yaml
from common.enums import WalnutSideEnum
from common.interfaces import (
    IAppConfig,
    DatabaseConfig,
    CameraConfig,
    AlgorithmConfig,
    BasicSimilarityConfig,
    AdvancedSimilarityConfig,
    FinalSimilarityConfig,
)





class AppConfig(IAppConfig):
    def __init__(
        self,
        image_root: str,
        database: dict,
        cameras: Optional[dict] = None,
        algorithm: Optional[dict] = None,
    ) -> None:
        self._image_root: str = image_root
        self._database: DatabaseConfig = DatabaseConfig(**database)
        
        # Load algorithm configurations - fail if missing
        if algorithm is None:
            raise ValueError("Algorithm configuration is required in config.yml")
        
        basic_config = algorithm.get("basic")
        if basic_config is None:
            raise ValueError("Algorithm 'basic' configuration is required in config.yml")
        
        advanced_config = algorithm.get("advanced")
        if advanced_config is None:
            raise ValueError("Algorithm 'advanced' configuration is required in config.yml")
        
        final_config = algorithm.get("final")
        if final_config is None:
            raise ValueError("Algorithm 'final' configuration is required in config.yml")
        
        self._algorithm: AlgorithmConfig = AlgorithmConfig(
            basic=BasicSimilarityConfig(**basic_config),
            advanced=AdvancedSimilarityConfig(**advanced_config),
            final=FinalSimilarityConfig(**final_config),
        )
        
        # Load camera configurations
        self._cameras: Dict[WalnutSideEnum, CameraConfig] = {}
        if cameras:
            side_mapping = {
                "FRONT": WalnutSideEnum.FRONT,
                "BACK": WalnutSideEnum.BACK,
                "LEFT": WalnutSideEnum.LEFT,
                "RIGHT": WalnutSideEnum.RIGHT,
                "TOP": WalnutSideEnum.TOP,
                "DOWN": WalnutSideEnum.DOWN,
            }
            for side_name, camera_data in cameras.items():
                side_enum = side_mapping.get(side_name.upper())
                if side_enum:
                    self._cameras[side_enum] = CameraConfig(**camera_data)

    @property
    def image_root(self) -> str:
        return self._image_root

    @property
    def database(self) -> DatabaseConfig:
        return self._database

    @property
    def algorithm(self) -> AlgorithmConfig:
        return self._algorithm

    @property
    def cameras(self) -> Dict[WalnutSideEnum, CameraConfig]:
        """Get camera configurations by side."""
        return self._cameras

    def get_camera_config(self, side: WalnutSideEnum) -> Optional[CameraConfig]:
        """Get camera configuration for a specific side."""
        return self._cameras.get(side)

    @classmethod
    def load_from_yaml(cls, yaml_path: Path) -> "AppConfig":
        with open(yaml_path, "r") as f:
            cfg = yaml.safe_load(f)
        return cls(**cfg)
