# src/config/config.py
from pathlib import Path
from dataclasses import dataclass
import yaml  # type: ignore[import-untyped]


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    host: str
    port: int
    database: str
    user: str
    password: str


class AppConfig:
    def __init__(
        self,
        image_root: str,
        database: dict,
    ) -> None:
        self.image_root = image_root
        self.database = DatabaseConfig(**database)

    @classmethod
    def load_from_yaml(cls, yaml_path: Path) -> "AppConfig":
        with open(yaml_path, "r") as f:
            cfg = yaml.safe_load(f)
        return cls(**cfg)
