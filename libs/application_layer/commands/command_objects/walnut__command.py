# application_layer/commands/command_objects/walnut_command.py
from dataclasses import dataclass, field
from typing import Optional

from .base__command import ICommand


@dataclass
class CreateFakeWalnutCommand(ICommand):
    walnut_id: str = ""
    description: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.walnut_id:
            raise ValueError("walnut_id is required")


@dataclass
class CreateWalnutFromImagesCommand(ICommand):
    walnut_id: str = ""
    description: Optional[str] = None
    save_intermediate_results: bool = False

    def __post_init__(self) -> None:
        if not self.walnut_id:
            raise ValueError("walnut_id is required")


@dataclass
class CompareWalnutsCommand(ICommand):
    """
    Command to compare walnuts and calculate similarity scores.
    
    Args:
        walnut_ids: Optional list of walnut IDs to compare. If None or empty, compares all walnuts.
    """
    walnut_ids: Optional[list[str]] = field(default_factory=lambda: None)
    width_weight: float = 0.0
    height_weight: float = 0.0
    thickness_weight: float = 0.0
