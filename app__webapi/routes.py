# app__webapi/routes.py
"""Route constants for WebAPI endpoints."""
from typing import Final

# Base API prefix
API_V1_PREFIX: Final[str] = "/api/v1"

# Walnut pairings routes
WALNUT_PAIRINGS_BASE: Final[str] = f"{API_V1_PREFIX}/walnut-pairings"
WALNUT_PAIRINGS_LIST: Final[str] = "/"
WALNUT_PAIRINGS_BY_WALNUT: Final[str] = "/walnut/{{walnut_id}}"
WALNUT_PAIRINGS_SPECIFIC: Final[str] = "/walnut/{{walnut_id}}/compared/{{compared_walnut_id}}"

