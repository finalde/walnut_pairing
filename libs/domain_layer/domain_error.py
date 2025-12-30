# domain_layer/domain_error.py
from abc import ABC


class DomainError(ABC):
    def __init__(self, message: str) -> None:
        self.message: str = message

    def __str__(self) -> str:
        return self.message


class ValidationError(DomainError):
    pass


class MissingSideError(ValidationError):
    def __init__(self, missing_sides: list[str]) -> None:
        self.missing_sides: list[str] = missing_sides
        super().__init__(f"Walnut must have all 6 sides. Missing: {', '.join(missing_sides)}")


class InvalidImageError(ValidationError):
    def __init__(self, side: str, reason: str) -> None:
        self.side: str = side
        self.reason: str = reason
        super().__init__(f"Invalid image for side {side}: {reason}")
