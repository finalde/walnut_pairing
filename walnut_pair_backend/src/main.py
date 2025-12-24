from src.business_layers.walnut_bl import WalnutBL
import sys
import os
import yaml
from pprint import pprint
from pathlib import Path
from src.common.app_config import AppConfig  # pyright: ignore[reportMissingImports]
def main():
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / "config.yml"
    config = AppConfig.load_from_yaml(config_path)

if __name__ == "__main__":
    main()
