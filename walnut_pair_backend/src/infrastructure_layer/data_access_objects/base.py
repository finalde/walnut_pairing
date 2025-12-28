# src/infrastructure_layer/data_access_objects/base.py
"""Base class for SQLAlchemy ORM models."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass

