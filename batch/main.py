# batch/main.py
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from common.logger import configure_logging, get_logger

from batch.application import Application
from batch.di_container import Container, bootstrap_container


async def main_async() -> None:
    configure_logging(log_level="INFO")
    logger = get_logger(__name__)
    container: Container | None = None
    try:
        config_path = project_root / "batch/config.yml"

        container = bootstrap_container()
        container.config_path.from_value(str(config_path))

        app: Application = container.application()
        await app.run_async()
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    finally:
        # Clean up session and engine
        if container is not None:
            try:
                from sqlalchemy.ext.asyncio import AsyncSession
                session = container.session()
                if session is not None and isinstance(session, AsyncSession):
                    await session.close()
                session_factory = container.session_factory()
                if session_factory is not None and hasattr(session_factory, "engine"):
                    await session_factory.engine.dispose(close=True)
            except Exception as cleanup_error:
                logger.warning(f"Error during cleanup: {cleanup_error}")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
