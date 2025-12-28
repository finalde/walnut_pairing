# src/application/application.py
"""Main application layer - orchestrates business logic."""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.business_layers.walnut_bl import IWalnutBL


class IApplication(ABC):
    """Interface for the main application layer."""

    @abstractmethod
    def run(self) -> None:
        """Run the main application logic."""
        pass


class Application(IApplication):
    """Main application class that orchestrates business logic."""

    def __init__(self, walnut_bl: "IWalnutBL") -> None:
        """
        Initialize the application with business logic dependencies.

        Args:
            walnut_bl: Walnut business logic layer
        """
        self.walnut_bl = walnut_bl

    def run(self) -> None:
        """Run the main application logic."""
        # Generate embeddings
        self.walnut_bl.generate_embeddings()

        # Test creating and saving a fake walnut with images and embeddings
        print("\n--- Testing DB Writer ---")
        fake_walnut = self.walnut_bl.create_and_save_fake_walnut("WALNUT-TEST-001")
        print(f"Saved walnut: {fake_walnut.id}")
        print(f"Number of images: {len(fake_walnut.images)}")
        for img in fake_walnut.images:
            print(
                f"  - {img.side}: image_id={img.id}, "
                f"embedding_id={img.embedding.id if img.embedding else None}"
            )

