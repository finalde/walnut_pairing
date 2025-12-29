# batch/main.py
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from batch.application import IApplication
from batch.di_container import Container


def main() -> None:
    config_path = project_root / "batch/config.yml"
    
    container = Container()
    container.config_path.from_value(str(config_path))
    
    app: IApplication = Container.application.__get__(container, Container)()
    app.run()


if __name__ == "__main__":
    main()
