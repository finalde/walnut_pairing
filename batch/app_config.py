# batch/app_config.py
from pathlib import Path
from dataclasses import dataclass
import yaml

from common.interfaces import IAppConfig


@dataclass
class DatabaseConfig:
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
        self._image_root: str = image_root
        self._database: DatabaseConfig = DatabaseConfig(**database)

    @property
    def image_root(self) -> str:
        return self._image_root

    @property
    def database(self) -> DatabaseConfig:
        return self._database

    @classmethod
    def load_from_yaml(cls, yaml_path: Path) -> "AppConfig":
        with open(yaml_path, "r") as f:
            cfg = yaml.safe_load(f)
        return cls(**cfg)

