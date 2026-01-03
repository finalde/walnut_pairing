# application_layer/commands/command_objects/walnut_command.py
from dataclasses import dataclass, field
from typing import Optional

from common.enums import ComparisonModeEnum
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
        comparison_mode: Mode of comparison (basic_only, advanced_only, or both)
        width_weight: Weight for width in basic similarity calculation
        height_weight: Weight for height in basic similarity calculation
        thickness_weight: Weight for thickness in basic similarity calculation
        front_weight: Weight for front side in advanced similarity calculation
        back_weight: Weight for back side in advanced similarity calculation
        left_weight: Weight for left side in advanced similarity calculation
        right_weight: Weight for right side in advanced similarity calculation
        top_weight: Weight for top side in advanced similarity calculation
        down_weight: Weight for down side in advanced similarity calculation
        basic_weight: Weight for basic similarity in final calculation
        advanced_weight: Weight for advanced similarity in final calculation
        skip_advanced_threshold: Skip advanced calculation if basic similarity is below this threshold
    """
    walnut_ids: Optional[list[str]] = field(default_factory=lambda: None)
    comparison_mode: ComparisonModeEnum = ComparisonModeEnum.BOTH
    # Basic similarity weights
    width_weight: float = 0.0
    height_weight: float = 0.0
    thickness_weight: float = 0.0
    # Advanced similarity weights
    front_weight: float = 0.0
    back_weight: float = 0.0
    left_weight: float = 0.0
    right_weight: float = 0.0
    top_weight: float = 0.0
    down_weight: float = 0.0
    # Final similarity weights
    basic_weight: float = 0.0
    advanced_weight: float = 0.0
    # Threshold
    skip_advanced_threshold: float = 0.3
