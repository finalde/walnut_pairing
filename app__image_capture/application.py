# app__image_capture/application.py
"""Image capture application orchestration."""
from application_layer.commands.command_dispatcher import ICommandDispatcher
from application_layer.commands.command_objects.image_capture__command import ImageCaptureCommand
from application_layer.queries.camera__query import ICameraQuery
from common.interfaces import IAppConfig
from common.logger import get_logger


class Application:
    """Image capture application."""

    def __init__(
        self,
        command_dispatcher: ICommandDispatcher,
        camera_query: ICameraQuery,
        app_config: IAppConfig,  # ImageCaptureAppConfig
    ) -> None:
        """
        Initialize the application.
        
        Args:
            command_dispatcher: Command dispatcher for executing commands
            camera_query: Camera query service for scanning cameras
            app_config: Application configuration
        """
        self.command_dispatcher: ICommandDispatcher = command_dispatcher
        self.camera_query: ICameraQuery = camera_query
        self.app_config: IAppConfig = app_config
        self.logger = get_logger(__name__)

    async def capture_async(self) -> None:
        """
        Handle capture command: scan for cameras and capture from all available cameras simultaneously.
        """
        # Step 1: Scan for available cameras
        self.logger.info("Scanning for available cameras...")
        # Update max_scan_index in camera_query if needed
        if hasattr(self.camera_query, 'max_scan_index'):
            self.camera_query.max_scan_index = self.app_config.scan.max_index
        available_cameras = await self.camera_query.scan_available_cameras_async()
        
        if not available_cameras:
            self.logger.error("No cameras found. Please check camera connections.")
            print("Error: No cameras found.")
            return
        
        num_cameras = len(available_cameras)
        self.logger.info(f"Found {num_cameras} camera(s): {available_cameras}")
        print(f"Found {num_cameras} camera(s): {available_cameras}")
        
        # Step 2: Get roles from config (use first N roles where N = number of cameras)
        all_roles = self.app_config.camera_roles.roles
        roles_to_use = all_roles[:num_cameras]
        
        if num_cameras > len(all_roles):
            self.logger.warning(
                f"Found {num_cameras} cameras but only {len(all_roles)} roles defined. "
                f"Using first {len(all_roles)} cameras."
            )
            roles_to_use = all_roles
            available_cameras = available_cameras[:len(all_roles)]
        
        # Step 3: Map cameras to roles (first camera -> first role, etc.)
        device_indices: dict[str, int] = {}
        for i, role in enumerate(roles_to_use):
            device_indices[role] = available_cameras[i]
        
        self.logger.info(f"Mapping cameras to roles: {device_indices}")
        print(f"Mapping cameras to roles: {device_indices}")
        
        # Step 4: Auto-generate capture ID (use timestamp)
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pad_width = self.app_config.file_naming.id_padding_width
        # Use a simple counter based on timestamp seconds
        capture_id = timestamp
        
        # Step 5: Create and dispatch command
        command = ImageCaptureCommand(
            capture_id=capture_id,
            roles=roles_to_use,
            device_indices=device_indices,
        )
        
        # Dispatch command
        self.logger.info(f"Capturing images with ID: {capture_id}")
        print(f"Capturing images with ID: {capture_id}")
        await self.command_dispatcher.dispatch_async(command)
        self.logger.info("Capture completed")
        print("Capture completed successfully!")
