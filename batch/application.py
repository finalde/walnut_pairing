# batch/application.py
"""Batch job application layer - orchestrates batch processing logic."""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import sys
from pathlib import Path

# Add libs to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "libs"))

if TYPE_CHECKING:
    from src.application_layer.walnut__al import IWalnutAL


class IApplication(ABC):
    """Interface for the batch application layer."""

    @abstractmethod
    def run(self) -> None:
        """Run the batch job logic."""
        pass


class Application(IApplication):
    """Batch application class that orchestrates batch processing."""

    def __init__(self, walnut_al: "IWalnutAL") -> None:
        """
        Initialize the batch application with application layer dependencies.

        Args:
            walnut_al: Walnut application layer
        """
        self.walnut_al: "IWalnutAL" = walnut_al

    def run(self) -> None:
        """Run the batch job logic."""
        # Generate embeddings
        self.walnut_al.generate_embeddings()

        # Test creating and saving a fake walnut with images and embeddings
        print("\n--- Testing DB Writer (Fake Data) ---")
        fake_walnut = self.walnut_al.create_and_save_fake_walnut("WALNUT-TEST-001")
        print(f"Saved walnut: {fake_walnut.id}")
        print(f"Number of images: {len(fake_walnut.images)}")
        for img in fake_walnut.images:
            print(
                f"  - {img.side}: image_id={img.id}, "
                f"embedding_id={img.embedding.id if img.embedding else None}"
            )

        # Test loading walnut from filesystem and saving to database
        print("\n--- Testing Load from Filesystem ---")
        try:
            loaded_walnut = self.walnut_al.load_and_save_walnut_from_filesystem("0001")
            print(f"Loaded and saved walnut: {loaded_walnut.id}")
            print(f"Number of images: {len(loaded_walnut.images)}")
            for img in loaded_walnut.images:
                print(
                    f"  - {img.side}: image_id={img.id}, "
                    f"embedding_id={img.embedding.id if img.embedding else None}"
                )
        except Exception as e:
            print(f"Error loading walnut from filesystem: {e}")
            import traceback
            traceback.print_exc()
