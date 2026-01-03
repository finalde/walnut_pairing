# app__webapi/main.py
"""FastAPI web application entry point."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app__webapi.dependencies import get_container, shutdown_container
from app__webapi.routes import walnuts


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Walnut Pairing API",
        description="API for walnut pairing and image processing",
        version="1.0.0",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(walnuts.router, prefix="/api/v1", tags=["walnuts"])

    # Startup and shutdown events
    @app.on_event("startup")
    async def startup_event() -> None:
        """Initialize DI container on startup."""
        get_container()

    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        """Clean up resources on shutdown."""
        shutdown_container()

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
