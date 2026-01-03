# app__image_capture/di_container.py
"""Image capture application DI container."""
from pathlib import Path
from typing import TYPE_CHECKING

from dependency_injector import containers, providers

from application_layer.commands.command_dispatcher import CommandDispatcher, ICommandDispatcher
from application_layer.commands.command_handlers.image_capture__command_handler import (
    ImageCaptureCommandHandler,
)
from application_layer.queries.camera__query import CameraQuery, ICameraQuery
from common.di_container import DependencyProviderWrapper
from common.di_registry import DIRegistry, Scope
from infrastructure_layer.file_writers import ImageFileWriter, IImageFileWriter
from infrastructure_layer.services.camera__service import CameraService, ICameraService

if TYPE_CHECKING:
    pass


def _register_dependencies() -> None:
    """Register all dependencies with their scopes in DIRegistry."""
    # Register infrastructure services as Singleton
    DIRegistry.register(ICameraService, CameraService, Scope.SINGLETON)
    DIRegistry.register(IImageFileWriter, ImageFileWriter, Scope.SINGLETON)
    
    # Register application layer queries as Singleton
    DIRegistry.register(ICameraQuery, CameraQuery, Scope.SINGLETON)


# Register dependencies before creating the container
_register_dependencies()


class ImageCaptureContainer(containers.DeclarativeContainer):
    """
    Image capture application DI container.
    
    Dependencies are registered in DIRegistry with scopes using:
        DIRegistry.register(IInterface, Implementation, Scope.SINGLETON)
    """

    # Configuration
    config_path = providers.Configuration()
    
    # App config (will be set in bootstrap_container)
    # This is a Configuration provider for the ImageCaptureCommandHandler
    app_config_provider = providers.Configuration()
    
    # IAppConfig provider (for resolving IAppConfig interface)
    # This will be set in bootstrap_container to the actual ImageCaptureAppConfig instance
    app_config = providers.Singleton(lambda: None)  # Placeholder, will be overridden

    # Self reference for container injection
    __self__ = providers.Self()

    # Infrastructure services (from DIRegistry)
    camera_service = providers.Singleton(
        lambda: DIRegistry.get(ICameraService)(),
    )

    image_file_writer = providers.Singleton(
        lambda: DIRegistry.get(IImageFileWriter)(),
    )

    # Application queries (from DIRegistry)
    camera_query = providers.Singleton(
        CameraQuery,
        camera_service=camera_service,
        max_scan_index=15,  # Can be read from config
    )

    # Command handler
    image_capture_command_handler = providers.Singleton(
        ImageCaptureCommandHandler,
        camera_service=camera_service,
        image_file_writer=image_file_writer,
        app_config=app_config_provider,  # Use app_config_provider
    )

    # Command dispatcher
    command_dispatcher = providers.Singleton(
        lambda container: CommandDispatcher.create_with_handlers(
            dependency_provider=DependencyProviderWrapper(container)
        ),
        container=__self__,
    )


def bootstrap_container(config_path: Path) -> ImageCaptureContainer:
    """
    Bootstrap and return the image capture container.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Bootstrapped container
    """
    # Load app config first
    from app__image_capture.app_config import ImageCaptureAppConfig
    app_config = ImageCaptureAppConfig.load_from_yaml(config_path)
    
    # Create container
    container = ImageCaptureContainer()
    
    # Register app_config in container so it can be resolved by DI
    # Override the app_config provider to return the actual instance
    from common.interfaces import IAppConfig
    container.app_config.override(providers.Object(app_config))
    
    # Also set app_config_provider for ImageCaptureCommandHandler
    container.app_config_provider.override(providers.Object(app_config))
    
    # Update camera_query with max_scan_index from config
    max_scan_index = app_config.scan.max_index
    container.camera_query.override(
        providers.Factory(
            CameraQuery,
            camera_service=container.camera_service,
            max_scan_index=max_scan_index,
        )
    )
    
    # Create command handler with app_config
    image_capture_handler = ImageCaptureCommandHandler(
        camera_service=container.camera_service(),
        image_file_writer=container.image_file_writer(),
        app_config=app_config,
    )
    
    # Register handler in dispatcher manually
    from application_layer.commands.command_objects.image_capture__command import ImageCaptureCommand
    dispatcher = container.command_dispatcher()
    dispatcher.register_handler(ImageCaptureCommand, image_capture_handler)
    
    return container

