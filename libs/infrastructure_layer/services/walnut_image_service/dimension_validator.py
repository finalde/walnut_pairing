# infrastructure_layer/services/walnut_image_service/dimension_validator.py


class DimensionValidator:
    """
    Validates technical aspects of image processing (not business rules).
    Business rules about dimension ranges are in WalnutDimensionValueObject.
    """

    def __init__(
        self,
        min_bbox_ratio: float = 0.2,
        max_bbox_ratio: float = 0.8,
    ) -> None:
        self.min_bbox_ratio: float = min_bbox_ratio
        self.max_bbox_ratio: float = max_bbox_ratio

    def validate_pixel_size(self, bbox_width_px: float, bbox_height_px: float, image_width: int, image_height: int) -> bool:
        """
        Technical validation: bounding box is reasonable size relative to image.
        This is a technical constraint, not a business rule.
        """
        width_ratio = bbox_width_px / image_width if image_width > 0 else 0.0
        height_ratio = bbox_height_px / image_height if image_height > 0 else 0.0

        return (
            self.min_bbox_ratio <= width_ratio <= self.max_bbox_ratio
            and self.min_bbox_ratio <= height_ratio <= self.max_bbox_ratio
        )

