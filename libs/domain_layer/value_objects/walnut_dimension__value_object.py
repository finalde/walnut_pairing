# domain_layer/value_objects/walnut_dimension__value_object.py
from dataclasses import dataclass

from common.either import Either, Left, Right
from domain_layer.domain_error import DomainError, ValidationError


@dataclass(frozen=True)
class WalnutDimensionValueObject:
    """
    Value object representing walnut physical dimensions in millimeters.

    Business invariants:
    - All dimensions must be positive
    - All dimensions must be within valid walnut size range (20-500mm)
    
    Domain semantics:
    - width: measured from FRONT/BACK/TOP/DOWN views
    - height: measured from FRONT/BACK/LEFT/RIGHT views
    - thickness: measured from LEFT/RIGHT/TOP/DOWN views
    """

    width_mm: float
    height_mm: float
    thickness_mm: float

    # Business constants - stable domain rules
    MIN_MM: float = 20.0
    MAX_MM: float = 500.0

    @classmethod
    def create(cls, width_mm: float, height_mm: float, thickness_mm: float) -> Either["WalnutDimensionValueObject", DomainError]:
        """
        Create walnut dimensions value object with validation.

        Business rules:
        - All dimensions must be positive
        - All dimensions must be within valid walnut size range
        """
        # Check all dimensions are positive
        if min(width_mm, height_mm, thickness_mm) <= 0:
            return Left(ValidationError("All dimensions must be positive"))

        # Check each dimension is within valid range
        for name, value in {
            "width": width_mm,
            "height": height_mm,
            "thickness": thickness_mm,
        }.items():
            if not (cls.MIN_MM <= value <= cls.MAX_MM):
                return Left(
                    ValidationError(f"{name.capitalize()} {value}mm is outside valid range [{cls.MIN_MM}, {cls.MAX_MM}]mm")
                )
        
        return Right(cls(width_mm=width_mm, height_mm=height_mm, thickness_mm=thickness_mm))
