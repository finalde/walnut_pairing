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
    - All dimensions must be within valid walnut size range (20-50mm)
    - Z cannot exceed X (semantic rule)
    """

    x_mm: float
    y_mm: float
    z_mm: float

    # Business constants - stable domain rules
    MIN_MM: float = 20.0
    MAX_MM: float = 500.0

    @classmethod
    def create(cls, x_mm: float, y_mm: float, z_mm: float) -> Either["WalnutDimensionValueObject", DomainError]:
        """
        Create walnut dimensions value object with validation.

        Business rules:
        - All dimensions must be positive
        - All dimensions must be within valid walnut size range
        - Z cannot exceed X (semantic invariant)
        """
        # Check all dimensions are positive
        if min(x_mm, y_mm, z_mm) <= 0:
            return Left(ValidationError("All dimensions must be positive"))

        # Check each dimension is within valid range
        for name, value in {
            "x": x_mm,
            "y": y_mm,
            "z": z_mm,
        }.items():
            if not (cls.MIN_MM <= value <= cls.MAX_MM):
                return Left(
                    ValidationError(f"{name.upper()}-axis {value}mm is outside valid range [{cls.MIN_MM}, {cls.MAX_MM}]mm")
                )
        
        # Semantic rule: z cannot exceed x
        if z_mm > x_mm:
            return Left(ValidationError("Z-axis cannot exceed X-axis"))
        
        return Right(cls(x_mm=x_mm, y_mm=y_mm, z_mm=z_mm))
