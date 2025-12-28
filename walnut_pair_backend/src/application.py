# src/application.py
"""Main application layer - orchestrates business logic."""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.application_layer.walnut_al import IWalnutAL


class IApplication(ABC):
    """Interface for the main application layer."""

    @abstractmethod
    def run(self) -> None:
        """Run the main application logic."""
        pass


class Application(IApplication):
    """Main application class that orchestrates business logic."""

    def __init__(self, walnut_al: "IWalnutAL") -> None:
        """
        Initialize the application with application layer dependencies.

        Args:
            walnut_al: Walnut application layer
        """
        self.walnut_al: "IWalnutAL" = walnut_al

    def run(self) -> None:
        """Run the main application logic."""
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

