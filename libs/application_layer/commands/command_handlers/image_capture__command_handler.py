# application_layer/commands/command_handlers/image_capture__command_handler.py
"""Command handler for image capture."""
from pathlib import Path
from typing import Dict, Optional

import numpy as np

from application_layer.commands.command_handlers.base__command_handler import ICommandHandler
from application_layer.commands.command_objects.image_capture__command import ImageCaptureCommand
from common.interfaces import IAppConfig
from common.logger import get_logger
from common.utils import ROLE_SUFFIX
from infrastructure_layer.file_writers import IImageFileWriter
from infrastructure_layer.services.camera__service import CameraHandle, ICameraService


class ImageCaptureCommandHandler(ICommandHandler[ImageCaptureCommand]):
    """Handler for ImageCaptureCommand."""

    def __init__(
        self,
        camera_service: ICameraService,
        image_file_writer: IImageFileWriter,
        app_config: IAppConfig,
    ) -> None:
        """
        Initialize the command handler.
        
        Args:
            camera_service: Camera service for capturing frames
            image_file_writer: File writer for saving images
            app_config: Application configuration
        """
        self.camera_service: ICameraService = camera_service
        self.image_file_writer: IImageFileWriter = image_file_writer
        self.app_config: IAppConfig = app_config
        self.logger = get_logger(__name__)
        self._opened_cameras: Dict[str, CameraHandle] = {}  # Track opened cameras by role

    async def handle_async(self, command: ImageCaptureCommand) -> None:
        """
        Handle image capture command.
        
        Args:
            command: ImageCaptureCommand with capture_id, roles, and device_indices
        """
        try:
            # Get roles to capture (use all roles from config if not specified)
            roles = command.roles if command.roles else self._get_all_roles()
            
            # Ensure directories exist
            image_root = Path(self.app_config.image_root)
            await self.image_file_writer.ensure_directories_async(roles, str(image_root))
            
            # Open cameras for specified roles
            opened_roles: list[str] = []
            for role in roles:
                if role not in command.device_indices:
                    self.logger.warning(f"No device index specified for role {role}, skipping")
                    continue
                
                device_index = command.device_indices[role]
                width, height = self._get_resolution()
                
                camera = await self.camera_service.open_camera_async(
                    index=device_index,
                    width=width,
                    height=height,
                    buffer_size=self._get_buffer_size(),
                    fourcc=self._get_fourcc(),
                    auto_exposure=self._get_auto_exposure(),
                )
                
                if camera:
                    self._opened_cameras[role] = camera
                    opened_roles.append(role)
                    self.logger.info(f"Opened camera {device_index} for role {role}")
                else:
                    self.logger.error(f"Failed to open camera {device_index} for role {role}")
            
            if not opened_roles:
                self.logger.error("No cameras opened successfully")
                return
            
            # Capture frames from all opened cameras simultaneously
            import asyncio
            self.logger.info("Capturing frames from all cameras simultaneously...")
            
            async def capture_from_camera(role: str) -> Optional[tuple[str, np.ndarray]]:
                """Capture a frame from a single camera."""
                camera = self._opened_cameras[role]
                frame = await self.camera_service.capture_frame_async(camera)
                if frame is not None:
                    self.logger.info(f"Captured frame from {role}")
                    return (role, frame)
                else:
                    self.logger.warning(f"Failed to capture frame from role {role}")
                    return None
            
            # Capture from all cameras concurrently
            capture_tasks = [capture_from_camera(role) for role in opened_roles]
            capture_results = await asyncio.gather(*capture_tasks)
            
            # Filter out None results
            images_to_save: list[tuple[str, np.ndarray]] = [
                result for result in capture_results if result is not None
            ]
            
            # Save all images
            for role, frame in images_to_save:
                suffix = ROLE_SUFFIX.get(role, role)
                image_path = self.image_file_writer.build_image_path(
                    base_path=str(image_root),
                    role=role,
                    capture_id=command.capture_id,
                    suffix=suffix,
                )
                success = await self.image_file_writer.save_image_async(frame, image_path)
                if success:
                    self.logger.info(f"Saved image for role {role} to {image_path}")
                else:
                    self.logger.error(f"Failed to save image for role {role} to {image_path}")
            
        finally:
            # Close all opened cameras
            await self._close_all_cameras()

    def _get_all_roles(self) -> list[str]:
        """Get all roles from config."""
        # Try to get from app_config if it has camera_roles property
        if hasattr(self.app_config, "camera_roles") and hasattr(self.app_config.camera_roles, "roles"):
            return list(self.app_config.camera_roles.roles)
        # Fallback to default roles
        from common.utils import ROLES
        return list(ROLES)

    def _get_resolution(self) -> tuple[int, int]:
        """Get resolution from config."""
        # Try to get from app_config if it has capture property
        if hasattr(self.app_config, "capture") and hasattr(self.app_config.capture, "get_resolution"):
            return self.app_config.capture.get_resolution()
        # Default resolution
        return (640, 480)

    def _get_buffer_size(self) -> int:
        """Get buffer size from config."""
        # Try to get from app_config if it has capture property
        if hasattr(self.app_config, "capture") and hasattr(self.app_config.capture, "buffer_size"):
            return self.app_config.capture.buffer_size
        # Default buffer size
        return 1

    def _get_fourcc(self) -> str:
        """Get FourCC codec from config."""
        # Try to get from app_config if it has capture property
        if hasattr(self.app_config, "capture") and hasattr(self.app_config.capture, "fourcc"):
            return self.app_config.capture.fourcc
        # Default codec
        return "MJPG"

    def _get_auto_exposure(self) -> float:
        """Get auto exposure setting from config."""
        # Try to get from app_config if it has capture property
        if hasattr(self.app_config, "capture") and hasattr(self.app_config.capture, "auto_exposure"):
            return self.app_config.capture.auto_exposure
        # Default auto exposure
        return 0.75

    async def _close_all_cameras(self) -> None:
        """Close all opened cameras."""
        for role, camera in list(self._opened_cameras.items()):
            await self.camera_service.close_camera_async(camera)
            self.logger.info(f"Closed camera for role {role}")
        self._opened_cameras.clear()

