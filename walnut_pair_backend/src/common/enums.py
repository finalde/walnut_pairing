from enum import Enum

class WalnutSideEnum(Enum):
    FRONT = "front"
    BACK = "back"
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    DOWN = "down"

    @classmethod
    def list(cls):
        """Return all sides as a list of strings"""
        return [side.value for side in cls]