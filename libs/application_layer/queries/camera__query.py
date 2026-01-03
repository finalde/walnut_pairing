# application_layer/queries/camera__query.py
"""Query service for camera operations."""
from abc import ABC, abstractmethod
from typing import List

from infrastructure_layer.services.camera__service import ICameraService


class ICameraQuery(ABC):
    """Interface for camera queries."""

    @abstractmethod
    async def scan_available_cameras_async(self) -> List[int]:
        """
        Scan for available cameras.
        
        Returns:
            List of available camera indices
        """
        pass

    @abstractmethod
    async def test_camera_async(self, index: int) -> bool:
        """
        Test if a specific camera is available.
        
        Args:
            index: Camera device index
            
        Returns:
            True if camera is available, False otherwise
        """
        pass


class CameraQuery(ICameraQuery):
    """Implementation of camera query service."""

    def __init__(self, camera_service: ICameraService, max_scan_index: int = 15) -> None:
        """
        Initialize the query service.
        
        Args:
            camera_service: Camera service for testing cameras
            max_scan_index: Maximum camera index to scan (default: 15)
        """
        self.camera_service: ICameraService = camera_service
        self.max_scan_index: int = max_scan_index

    async def scan_available_cameras_async(self) -> List[int]:
        """Scan for available cameras."""
        return await self.camera_service.scan_available_cameras_async(self.max_scan_index)

    async def test_camera_async(self, index: int) -> bool:
        """Test if a specific camera is available."""
        return await self.camera_service.test_camera_available_async(index)

