# webapi/dependencies.py
"""Dependency injection setup for FastAPI."""
from pathlib import Path
from typing import Optional

from common.di_container import Container

# Global container instance
_container: Optional[Container] = None


def get_container() -> Container:
    """Get or create the DI container."""
    global _container
    if _container is None:
        project_root = Path(__file__).resolve().parent.parent
        config_path = project_root / "webapi" / "config.yml"
        
        _container = Container()
        _container.config_path.from_value(config_path)
    return _container


def shutdown_container() -> None:
    """Clean up container resources."""
    global _container
    if _container is not None:
        db_connection = _container.db_connection()
        if db_connection:
            db_connection.close()
        _container = None

