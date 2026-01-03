# app__webapi/main.py
"""FastAPI web application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app__webapi.controllers import walnut_pairings__controller
from app__webapi.dependencies import get_container, shutdown_container


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    get_container()
    yield
    # Shutdown
    shutdown_container()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Walnut Pairing API",
        description="API for walnut pairing and image processing. Provides endpoints to query walnut pairing results based on similarity scores.",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",  # Swagger UI
        redoc_url="/redoc",  # ReDoc
        openapi_url="/openapi.json",  # OpenAPI schema
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
    from app__webapi.routes import WALNUT_PAIRINGS_BASE
    app.include_router(walnut_pairings__controller.router, prefix=WALNUT_PAIRINGS_BASE)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
