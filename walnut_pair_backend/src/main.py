from pathlib import Path
from src.common.app_config import AppConfig  # pyright: ignore[reportMissingImports]


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    config_path : Path = project_root / "config.yml"
    app_config : AppConfig = AppConfig.load_from_yaml(config_path)
    print(app_config)


if __name__ == "__main__":
    main()
