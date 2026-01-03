# batch/main.py
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from common.logger import configure_logging, get_logger

from batch.application import IApplication
from batch.di_container import bootstrap_container


def main() -> None:
    configure_logging(log_level="INFO")
    logger = get_logger(__name__)
    try:
        config_path = project_root / "batch/config.yml"

        container = bootstrap_container()
        container.config_path.from_value(str(config_path))

        app: IApplication = container.application()
        app.run()
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
