# infrastructure_layer/services/camera__service.py
"""Camera service for capturing images from cameras."""
import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional

import cv2
import numpy as np

from common.logger import get_logger

# Type alias for camera handle
CameraHandle = cv2.VideoCapture


class ICameraService(ABC):
    """Interface for camera operations."""

    @abstractmethod
    async def test_camera_available_async(self, index: int) -> bool:
        """
        Quick test if camera index is available.
        
        Args:
            index: Camera device index
            
        Returns:
            True if camera is available, False otherwise
        """
        pass

    @abstractmethod
    async def open_camera_async(
        self, index: int, width: int, height: int, buffer_size: int = 1, fourcc: str = "MJPG", auto_exposure: float = 0.75
    ) -> Optional[CameraHandle]:
        """
        Open a camera with specified settings.
        
        Args:
            index: Camera device index
            width: Frame width
            height: Frame height
            buffer_size: Buffer size (1 for low latency)
            fourcc: FourCC codec (default: "MJPG")
            auto_exposure: Auto exposure setting (0.75 = auto)
            
        Returns:
            CameraHandle if successful, None otherwise
        """
        pass

    @abstractmethod
    async def capture_frame_async(self, camera: CameraHandle) -> Optional[np.ndarray]:
        """
        Capture a single frame from the camera.
        
        Args:
            camera: Camera handle
            
        Returns:
            Frame as numpy array (BGR format) if successful, None otherwise
        """
        pass

    @abstractmethod
    async def close_camera_async(self, camera: CameraHandle) -> None:
        """
        Close and release a camera.
        
        Args:
            camera: Camera handle to close
        """
        pass

    @abstractmethod
    async def scan_available_cameras_async(self, max_index: int) -> List[int]:
        """
        Scan for available cameras.
        
        Args:
            max_index: Maximum camera index to scan (0 to max_index)
            
        Returns:
            List of available camera indices
        """
        pass


class CameraService(ICameraService):
    """Implementation of camera service using OpenCV."""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        # Reduce OpenCV log verbosity
        try:
            cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
        except Exception:
            pass

    async def test_camera_available_async(self, index: int) -> bool:
        """
        Quick test if camera index is available.
        
        Uses CAP_MSMF backend (Windows Media Foundation) for reliable testing,
        matching the working implementation pattern.
        """
        try:
            # Use MSMF backend for testing (more reliable on Windows)
            # Run in thread pool since cv2.VideoCapture is blocking
            cap = await asyncio.to_thread(cv2.VideoCapture, index, cv2.CAP_MSMF)
            if cap and cap.isOpened():
                await asyncio.to_thread(cap.release)
                self.logger.debug(f"Camera {index} is available (MSMF)")
                return True
        except Exception as e:
            self.logger.debug(f"Camera {index} test failed with MSMF: {e}")
            # Try fallback to CAP_ANY if MSMF fails (for non-Windows systems)
            try:
                cap = await asyncio.to_thread(cv2.VideoCapture, index, cv2.CAP_ANY)
                if cap and cap.isOpened():
                    await asyncio.to_thread(cap.release)
                    self.logger.debug(f"Camera {index} is available (CAP_ANY)")
                    return True
            except Exception:
                pass
        return False

    async def open_camera_async(
        self, index: int, width: int, height: int, buffer_size: int = 1, fourcc: str = "MJPG", auto_exposure: float = 0.75
    ) -> Optional[CameraHandle]:
        """Open camera with fallback backends."""
        backends = [cv2.CAP_MSMF, cv2.CAP_DSHOW, cv2.CAP_ANY]
        
        for backend in backends:
            try:
                # Try to open camera with this backend
                cap = await asyncio.to_thread(cv2.VideoCapture, index, backend)
                if cap and cap.isOpened():
                    # Configure camera settings
                    await asyncio.to_thread(cap.set, cv2.CAP_PROP_BUFFERSIZE, buffer_size)
                    await asyncio.to_thread(cap.set, cv2.CAP_PROP_FRAME_WIDTH, width)
                    await asyncio.to_thread(cap.set, cv2.CAP_PROP_FRAME_HEIGHT, height)
                    await asyncio.to_thread(cap.set, cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourcc))
                    await asyncio.to_thread(cap.set, cv2.CAP_PROP_AUTO_EXPOSURE, auto_exposure)
                    self.logger.info(f"Opened camera {index} with backend {backend}")
                    return cap
                else:
                    if cap:
                        await asyncio.to_thread(cap.release)
            except Exception as e:
                self.logger.warning(f"Failed to open camera {index} with backend {backend}: {e}")
                continue
        
        self.logger.error(f"Failed to open camera {index} with any backend")
        return None

    async def capture_frame_async(self, camera: CameraHandle) -> Optional[np.ndarray]:
        """Capture a single frame from the camera."""
        try:
            # Run read in thread pool since it's blocking
            ok, frame = await asyncio.to_thread(camera.read)
            if ok and frame is not None:
                return frame
            return None
        except Exception as e:
            self.logger.error(f"Error capturing frame: {e}")
            return None

    async def close_camera_async(self, camera: CameraHandle) -> None:
        """Close and release a camera."""
        try:
            await asyncio.to_thread(camera.release)
            self.logger.info("Camera closed")
        except Exception as e:
            self.logger.error(f"Error closing camera: {e}")

    async def scan_available_cameras_async(self, max_index: int) -> List[int]:
        """Scan for available cameras."""
        found: List[int] = []
        # Test camera indices 0 to max_index
        for i in range(max_index + 1):
            if await self.test_camera_available_async(i):
                found.append(i)
        return found

