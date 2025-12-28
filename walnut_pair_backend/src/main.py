from pathlib import Path
import sys

# Add parent directory to path to allow imports when running directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.application.application import IApplication
from src.common.di_container import Container


def main() -> None:
    """Main entry point using dependency injection container."""
    project_root: Path = Path(__file__).resolve().parent.parent
    config_path: Path = project_root / "config.yml"

    # Initialize dependency injection container
    container = Container()
    container.config_path.from_value(config_path)

    try:
        # Get application from container (all dependencies are auto-injected)
        app: IApplication = container.application()
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up database connection and session
        db_connection = container.db_connection()
        if db_connection:
            db_connection.close()
        
        # Note: SQLAlchemy sessions are created per operation and should be closed
        # The session factory manages session lifecycle


if __name__ == "__main__":
    main()
