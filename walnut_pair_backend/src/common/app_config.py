# src/config/config.py
from pathlib import Path
from dataclasses import dataclass
import yaml  # type: ignore[import-untyped]

from src.common.interfaces import IAppConfig


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    host: str
    port: int
    database: str
    user: str
    password: str


class AppConfig(IAppConfig):
    def __init__(
        self,
        image_root: str,
        database: dict,
    ) -> None:
        self._image_root = image_root
        self._database = DatabaseConfig(**database)

    @property
    def image_root(self) -> str:
        """Get the root path for images."""
        return self._image_root

    @property
    def database(self) -> DatabaseConfig:
        """Get the database configuration."""
        return self._database

    @classmethod
    def load_from_yaml(cls, yaml_path: Path) -> "AppConfig":
        with open(yaml_path, "r") as f:
            cfg = yaml.safe_load(f)
        return cls(**cfg)
