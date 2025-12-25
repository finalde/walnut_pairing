from pathlib import Path
import sys
from typing import Optional

import psycopg2
from psycopg2.extensions import connection

# Add parent directory to path to allow imports when running directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.common.app_config import AppConfig
from src.domain_layers.services.embedding_service import ImageEmbeddingService
from src.business_layers.walnut_bl import IWalnutBL, WalnutBL

db_connection: Optional[connection] = None
def main() -> None:
    try:
        project_root : Path = Path(__file__).resolve().parent.parent
        config_path : Path = project_root / "config.yml"
        app_config : AppConfig = AppConfig.load_from_yaml(config_path)
        db_connection : connection = psycopg2.connect(
            host=app_config.database.host,
            port=app_config.database.port,
            database=app_config.database.database,
            user=app_config.database.user,
            password=app_config.database.password)

        walnut_bl : IWalnutBL = WalnutBL(ImageEmbeddingService(), app_config, db_connection)
        walnut_bl.generate_embeddings()
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
    finally:
        if db_connection:
            db_connection.close()
if __name__ == "__main__":
    main()
