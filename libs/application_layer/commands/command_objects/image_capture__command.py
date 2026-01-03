# application_layer/commands/command_objects/image_capture__command.py
"""Command for capturing images from cameras."""
from dataclasses import dataclass, field
from typing import Dict, List

from .base__command import ICommand


@dataclass
class ImageCaptureCommand(ICommand):
    """Command to capture images from multiple cameras."""

    capture_id: str = ""
    roles: List[str] = field(default_factory=list)
    device_indices: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate command."""
        if not self.capture_id:
            raise ValueError("capture_id is required")

