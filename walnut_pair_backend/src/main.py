from pathlib import Path
import sys

# Add parent directory to path to allow imports when running directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.common.app_config import AppConfig
from src.domain_layers.services.embedding_service import ImageEmbeddingService
from src.business_layers.walnut_bl import IWalnutBL, WalnutBL

def main() -> None:
    project_root : Path = Path(__file__).resolve().parent.parent
    config_path : Path = project_root / "config.yml"
    app_config : AppConfig = AppConfig.load_from_yaml(config_path)
    walnut_bl : IWalnutBL = WalnutBL(ImageEmbeddingService(), app_config)
    walnut_bl.generate_embeddings()
if __name__ == "__main__":
    main()
