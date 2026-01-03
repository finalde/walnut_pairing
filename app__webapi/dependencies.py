# app__webapi/dependencies.py
"""FastAPI dependency injection setup with request scoping."""
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from application_layer.queries.walnut_comparison__query import IWalnutComparisonQuery
from app__webapi.di_container import WebAPIContainer, bootstrap_webapi_container

# Global container instance (Singleton scope)
_container: Optional[WebAPIContainer] = None


def get_container() -> WebAPIContainer:
    """Get or create the global DI container (Singleton scope)."""
    global _container
    if _container is None:
        project_root = Path(__file__).resolve().parent.parent
        config_path = project_root / "app__webapi" / "config.yml"
        _container = bootstrap_webapi_container(config_path)
    return _container


async def get_session(
    container: WebAPIContainer = Depends(get_container),
) -> AsyncGenerator[AsyncSession, None]:
    """
    Get async session for current request (Request scope).
    
    This dependency creates a new session per request and ensures
    it's properly closed after the request completes.
    """
    session = container.session()
    try:
        yield session
    finally:
        await session.close()


def get_walnut_comparison_query(
    session: AsyncSession = Depends(get_session),
    container: WebAPIContainer = Depends(get_container),
) -> IWalnutComparisonQuery:
    """
    Get walnut comparison query service for current request (Request scope).
    
    Creates a new query instance per request with the request-scoped session.
    """
    # Create a new reader with the request-scoped session
    from infrastructure_layer.db_readers import WalnutComparisonDBReader
    from application_layer.queries.walnut_comparison__query import WalnutComparisonQuery
    
    reader = WalnutComparisonDBReader(session)
    mapper = container.walnut_comparison_mapper()
    return WalnutComparisonQuery(comparison_reader=reader, comparison_mapper=mapper)


def shutdown_container() -> None:
    """Clean up container resources on shutdown."""
    global _container
    if _container is not None:
        try:
            session_factory = _container.session_factory()
            if session_factory is not None and hasattr(session_factory, "engine"):
                # Note: This is called during shutdown, so we can't use await
                # The engine will be disposed when the process exits
                pass
        except Exception:
            pass
        _container = None
