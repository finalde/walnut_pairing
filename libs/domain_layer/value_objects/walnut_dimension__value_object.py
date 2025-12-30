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
    - Height cannot exceed length (semantic rule)
    """

    length_mm: float
    width_mm: float
    height_mm: float

    # Business constants - stable domain rules
    MIN_MM: float = 20.0
    MAX_MM: float = 50.0

    @classmethod
    def create(cls, length_mm: float, width_mm: float, height_mm: float) -> Either["WalnutDimensionValueObject", DomainError]:
        """
        Create walnut dimensions value object with validation.
        
        Business rules:
        - All dimensions must be positive
        - All dimensions must be within valid walnut size range
        - Height cannot exceed length (semantic invariant)
        """
        # Check all dimensions are positive
        if min(length_mm, width_mm, height_mm) <= 0:
            return Left(ValidationError("All dimensions must be positive"))

        # Check each dimension is within valid range
        for name, value in {
            "length": length_mm,
            "width": width_mm,
            "height": height_mm,
        }.items():
            if not (cls.MIN_MM <= value <= cls.MAX_MM):
                return Left(ValidationError(f"{name.capitalize()} {value}mm is outside valid range [{cls.MIN_MM}, {cls.MAX_MM}]mm"))

        # Semantic rule: height cannot exceed length
        if height_mm > length_mm:
            return Left(ValidationError("Height cannot exceed length"))

        return Right(cls(length_mm=length_mm, width_mm=width_mm, height_mm=height_mm))

