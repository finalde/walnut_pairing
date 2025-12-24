# src/config/config.py
from pathlib import Path
import yaml

class AppConfig:
    def __init__(self, image_root: str):
        self.image_root: Path = Path(image_root)

    @classmethod
    def load_from_yaml(cls, yaml_path: Path):
        with open(yaml_path, "r") as f:
            cfg = yaml.safe_load(f)
        return cls(**cfg)
