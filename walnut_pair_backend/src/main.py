from pathlib import Path
import sys

# Add parent directory to path to allow imports when running directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.business_layers.walnut_bl import IWalnutBL
from src.common.di_container import Container


def main() -> None:
    """Main entry point using dependency injection container."""
    project_root: Path = Path(__file__).resolve().parent.parent
    config_path: Path = project_root / "config.yml"

    # Initialize dependency injection container
    container = Container()
    container.config_path.from_value(config_path)

    try:
        # Get business logic layer from container (all dependencies are auto-injected)
        walnut_bl : IWalnutBL = container.walnut_bl()
        walnut_bl.generate_embeddings()
        
        # Test creating and saving a fake walnut with images and embeddings
        print("\n--- Testing DB Writer ---")
        fake_walnut = walnut_bl.create_and_save_fake_walnut("WALNUT-TEST-001")
        print(f"Saved walnut: {fake_walnut.id}")
        print(f"Number of images: {len(fake_walnut.images)}")
        for img in fake_walnut.images:
            print(f"  - {img.side}: image_id={img.id}, embedding_id={img.embedding.id if img.embedding else None}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up database connection and session
        db_connection = container.db_connection()
        if db_connection:
            db_connection.close()
        
        # Note: SQLAlchemy sessions are created per operation and should be closed
        # The session factory manages session lifecycle


if __name__ == "__main__":
    main()
