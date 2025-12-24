from enum import Enum
from typing import List

class WalnutSideEnum(Enum):
    FRONT = "front"
    BACK = "back"
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    DOWN = "down"

    @classmethod
    def list(cls) -> List[str]:
        """Return all sides as a list of strings"""
        return [side.value for side in cls]