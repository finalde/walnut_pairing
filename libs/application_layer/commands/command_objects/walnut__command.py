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


@dataclass(kw_only=True)
class CompareWalnutsCommand(ICommand):
    """
    Command to compare walnuts and calculate similarity scores.
    
    All parameters must be provided explicitly - no default values.
    All values should come from config.
    
    Note: Inherits timestamp and user_id from ICommand (both have defaults).
    All comparison-specific fields are required and must come from config.
    
    Args:
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
        discriminative_power: Power transformation for embedding scores (higher = rarer high scores)
        min_expected_cosine: Minimum expected cosine similarity for normalization
        max_expected_cosine: Maximum expected cosine similarity for normalization
        walnut_ids: Optional list of walnut IDs to compare. If None or empty, compares all walnuts.
    """
    # All required fields (must come before optional fields with defaults)
    comparison_mode: ComparisonModeEnum
    # Basic similarity weights
    width_weight: float
    height_weight: float
    thickness_weight: float
    # Advanced similarity weights
    front_weight: float
    back_weight: float
    left_weight: float
    right_weight: float
    top_weight: float
    down_weight: float
    # Final similarity weights
    basic_weight: float
    advanced_weight: float
    # Threshold
    skip_advanced_threshold: float
    # Discriminative parameters for embedding comparison
    discriminative_power: float
    min_expected_cosine: float
    max_expected_cosine: float
    # Optional: list of walnut IDs to compare (None means compare all)
    walnut_ids: Optional[list[str]] = field(default_factory=lambda: None)
