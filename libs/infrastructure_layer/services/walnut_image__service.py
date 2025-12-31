# infrastructure_layer/services/walnut_image__service.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from common.enums import WalnutSideEnum
from domain_layer.domain_services.dimension__domain_service import ViewMeasurement
from domain_layer.value_objects.image__value_object import ImageValueObject

from .image_object__finder import IImageObjectFinder, ObjectDetectionResult


class IWalnutImageService(ABC):
    @abstractmethod
    def get_measurements_from_images(
        self,
        images: Dict[WalnutSideEnum, ImageValueObject],
        camera_distance_mm: float = 300.0,
        background_is_white: bool = True,
        intermediate_dir: Optional[str] = None,
    ) -> List[ViewMeasurement]:
        """
        Get raw pixel measurements from images using object finder.
        
        This is infrastructure layer - just returns raw measurements.
        Domain logic (mapping views to dimensions) is handled in domain layer.
        """
        pass


class WalnutImageService(IWalnutImageService):
    """Service for extracting measurements from walnut images."""

    def __init__(self, object_finder: IImageObjectFinder) -> None:
        """Initialize with an image object finder service."""
        self.object_finder: IImageObjectFinder = object_finder

    def get_measurements_from_images(
        self,
        images: Dict[WalnutSideEnum, ImageValueObject],
        camera_distance_mm: float = 300.0,
        background_is_white: bool = True,
        intermediate_dir: Optional[str] = None,
    ) -> List[ViewMeasurement]:
        """
        Get raw pixel measurements from images.
        
        Returns list of ViewMeasurement objects containing:
        - Side (view orientation)
        - Width and height in pixels
        - Camera distance in mm
        """
        measurements: List[ViewMeasurement] = []
        
        for side_enum, image_vo in images.items():
            # Determine intermediate directory for this specific image
            image_intermediate_dir = None
            if intermediate_dir:
                from pathlib import Path
                image_path = Path(image_vo.path)
                image_name = image_path.stem
                image_intermediate_dir = str(Path(intermediate_dir) / image_name)
            
            # Find object in image
            result: Optional[ObjectDetectionResult] = self.object_finder.find_object(
                image_vo.path,
                background_is_white=background_is_white,
                intermediate_dir=image_intermediate_dir,
            )
            
            if result and result.width_px > 0 and result.height_px > 0:
                camera_distance = image_vo.camera_distance_mm or camera_distance_mm
                measurements.append(
                    ViewMeasurement(
                        side=side_enum,
                        width_px=result.width_px,
                        height_px=result.height_px,
                        camera_distance_mm=camera_distance,
                    )
                )
        
        return measurements

