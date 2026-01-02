# infrastructure_layer/db_writers/walnut_comparison__db_writer.py
from abc import ABC, abstractmethod
from typing import List

from infrastructure_layer.data_access_objects.walnut_comparison__db_dao import WalnutComparisonDBDAO
from sqlalchemy.orm import Session


class IWalnutComparisonDBWriter(ABC):
    """Interface for writing walnut comparisons to database."""

    @abstractmethod
    def save(self, comparison_dao: WalnutComparisonDBDAO) -> WalnutComparisonDBDAO:
        """Save a new walnut comparison to the database."""
        pass

    @abstractmethod
    def save_or_update(self, comparison_dao: WalnutComparisonDBDAO) -> WalnutComparisonDBDAO:
        """Save or update a walnut comparison (upsert operation)."""
        pass

    @abstractmethod
    def bulk_save_or_update(self, comparison_daos: List[WalnutComparisonDBDAO]) -> List[WalnutComparisonDBDAO]:
        """Bulk save or update walnut comparisons (upsert operation)."""
        pass


class WalnutComparisonDBWriter(IWalnutComparisonDBWriter):
    """Implementation for writing walnut comparisons to database."""

    def __init__(self, session: Session) -> None:
        """
        Initialize with a SQLAlchemy session.
        
        Args:
            session: SQLAlchemy Session instance (injected via DI container)
        """
        self.session: Session = session

    def save(self, comparison_dao: WalnutComparisonDBDAO) -> WalnutComparisonDBDAO:
        """Save a new walnut comparison to the database."""
        self.session.add(comparison_dao)
        self.session.commit()
        self.session.refresh(comparison_dao)
        return comparison_dao

    def save_or_update(self, comparison_dao: WalnutComparisonDBDAO) -> WalnutComparisonDBDAO:
        """Save or update a walnut comparison (upsert operation)."""
        # Try to find existing comparison
        existing = (
            self.session.query(WalnutComparisonDBDAO)
            .filter_by(
                walnut_id=comparison_dao.walnut_id,
                compared_walnut_id=comparison_dao.compared_walnut_id,
            )
            .first()
        )

        if existing:
            # Update existing
            existing.width_diff_mm = comparison_dao.width_diff_mm
            existing.height_diff_mm = comparison_dao.height_diff_mm
            existing.thickness_diff_mm = comparison_dao.thickness_diff_mm
            existing.similarity_score = comparison_dao.similarity_score
            existing.width_weight = comparison_dao.width_weight
            existing.height_weight = comparison_dao.height_weight
            existing.thickness_weight = comparison_dao.thickness_weight
            existing.updated_by = comparison_dao.updated_by
            self.session.commit()
            self.session.refresh(existing)
            return existing
        else:
            # Insert new
            self.session.add(comparison_dao)
            self.session.commit()
            self.session.refresh(comparison_dao)
            return comparison_dao

    def bulk_save_or_update(self, comparison_daos: List[WalnutComparisonDBDAO]) -> List[WalnutComparisonDBDAO]:
        """Bulk save or update walnut comparisons (upsert operation)."""
        saved_comparisons: List[WalnutComparisonDBDAO] = []

        for comparison_dao in comparison_daos:
            # Try to find existing comparison
            existing = (
                self.session.query(WalnutComparisonDBDAO)
                .filter_by(
                    walnut_id=comparison_dao.walnut_id,
                    compared_walnut_id=comparison_dao.compared_walnut_id,
                )
                .first()
            )

            if existing:
                # Update existing
                existing.width_diff_mm = comparison_dao.width_diff_mm
                existing.height_diff_mm = comparison_dao.height_diff_mm
                existing.thickness_diff_mm = comparison_dao.thickness_diff_mm
                existing.similarity_score = comparison_dao.similarity_score
                existing.width_weight = comparison_dao.width_weight
                existing.height_weight = comparison_dao.height_weight
                existing.thickness_weight = comparison_dao.thickness_weight
                existing.updated_by = comparison_dao.updated_by
                saved_comparisons.append(existing)
            else:
                # Insert new
                self.session.add(comparison_dao)
                saved_comparisons.append(comparison_dao)

        # Commit all changes at once
        self.session.commit()

        # Refresh all saved comparisons
        for comparison in saved_comparisons:
            self.session.refresh(comparison)

        return saved_comparisons

