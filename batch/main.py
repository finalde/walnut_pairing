# batch/main.py
"""Batch job entry point."""
from pathlib import Path
import sys

# Add project root and libs to path (must be before importing batch.application)
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "libs"))

from batch.application import IApplication, Application
from src.common.di_container import Container


def main() -> None:
    """Main entry point for batch job using dependency injection container."""
    config_path: Path = project_root / "batch" / "config.yml"

    # Initialize dependency injection container
    container = Container()
    container.config_path.from_value(config_path)

    try:
        # Get application dependencies from container
        from src.application_layer.walnut__al import IWalnutAL
        walnut_al: IWalnutAL = container.walnut_al()
        
        # Create application instance
        app: IApplication = Application(walnut_al=walnut_al)
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
