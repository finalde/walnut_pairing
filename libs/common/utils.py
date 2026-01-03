# common/utils.py
"""Common utility functions."""
from typing import Final

# Camera roles
ROLES: Final[list[str]] = ["Front", "Back", "Left", "Right", "Top", "Down", "Additional1", "Additional2"]

# Role suffixes for file naming
ROLE_SUFFIX: Final[dict[str, str]] = {
    "Front": "F",
    "Back": "B",
    "Left": "L",
    "Right": "R",
    "Top": "T",
    "Down": "D",
    "Additional1": "A1",
    "Additional2": "A2",
}


def zero_pad_id(id_text: str, width: int = 4) -> str:
    """
    Extract numeric digits from id_text and zero-pad to specified width.
    
    Args:
        id_text: Text containing ID (e.g., "walnut_0001" or "0001")
        width: Desired width of padded ID (default: 4)
        
    Returns:
        Zero-padded ID string (e.g., "0001")
        
    Examples:
        zero_pad_id("walnut_0001", 4) -> "0001"
        zero_pad_id("5", 4) -> "0005"
        zero_pad_id("abc", 4) -> "0000"  # No digits found
    """
    digits = "".join(ch for ch in id_text if ch.isdigit())
    if not digits:
        return "".zfill(width)
    return digits.zfill(width)

