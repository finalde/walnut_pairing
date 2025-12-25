from pathlib import Path
import sys

# Add parent directory to path to allow imports when running directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.common.di_container import Container


def main() -> None:
    """Main entry point using dependency injection container."""
    project_root: Path = Path(__file__).resolve().parent.parent
    config_path: Path = project_root / "config.yml"

    # Initialize dependency injection container
    container = Container()
    container.config_path.from_value(config_path)

    try:
        # Get business logic layer from container (all dependencies are auto-injected)
        walnut_bl = container.walnut_bl()
        walnut_bl.generate_embeddings()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up database connection
        db_connection = container.db_connection()
        if db_connection:
            db_connection.close()


if __name__ == "__main__":
    main()
