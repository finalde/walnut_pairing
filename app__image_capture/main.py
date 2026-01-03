# app__image_capture/main.py
"""Image capture application entry point."""
import asyncio
import sys
from pathlib import Path

from common.logger import get_logger

from app__image_capture.app_config import ImageCaptureAppConfig
from app__image_capture.application import Application
from app__image_capture.di_container import bootstrap_container

logger = get_logger(__name__)


async def main_async() -> None:
    """Main async function."""
    # Load configuration
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / "app__image_capture" / "config.yml"
    
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    
    app_config = ImageCaptureAppConfig.load_from_yaml(config_path)
    
    # Bootstrap DI container
    container = bootstrap_container(config_path)
    
    # Create application
    application = Application(
        command_dispatcher=container.command_dispatcher(),
        camera_query=container.camera_query(),
        app_config=app_config,
    )
    
    # Run application (automatically captures from all available cameras)
    try:
        await application.capture_async()
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup if needed
        pass


def main() -> None:
    """Main entry point."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

