# common/constants.py
"""Application-wide constants to avoid magic strings."""

# Model names
DEFAULT_EMBEDDING_MODEL = "resnet50-imagenet"

# System user identifiers
SYSTEM_USER = "system"

# Image format fallback
UNKNOWN_IMAGE_FORMAT = "UNKNOWN"

# Database constraint names
CONSTRAINT_UQ_WALNUT_SIDE = "uq_walnut_side"
CONSTRAINT_UQ_WALNUT_COMPARISON = "uq_walnut_comparison"

# Database table names (to avoid magic strings in ForeignKey)
TABLE_WALNUT = "walnut"
TABLE_WALNUT_IMAGE = "walnut_image"
TABLE_WALNUT_IMAGE_EMBEDDING = "walnut_image_embedding"
TABLE_WALNUT_COMPARISON = "walnut_comparison"
