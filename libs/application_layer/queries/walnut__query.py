# application_layer/queries/walnut__query.py
from abc import ABC, abstractmethod
from typing import Optional, List
from pathlib import Path

from infrastructure_layer.db_readers import IWalnutDBReader
from application_layer.dtos.walnut__dto import WalnutDTO
from application_layer.mappers.walnut__mapper import IWalnutMapper
from common.interfaces import IAppConfig
from application_layer.services.walnut_image_loader import WalnutImageLoader


class IWalnutQuery(ABC):
    @abstractmethod
    def get_by_id(self, walnut_id: str) -> Optional[WalnutDTO]:
        pass

    @abstractmethod
    def get_all(self) -> List[WalnutDTO]:
        pass

    @abstractmethod
    def load_from_filesystem(self, walnut_id: str) -> Optional[WalnutDTO]:
        pass


class WalnutQuery(IWalnutQuery):
    def __init__(
        self,
        walnut_reader: IWalnutDBReader,
        walnut_mapper: IWalnutMapper,
        app_config: IAppConfig,
    ) -> None:
        self.walnut_reader: IWalnutDBReader = walnut_reader
        self.walnut_mapper: IWalnutMapper = walnut_mapper
        self.app_config: IAppConfig = app_config

    def get_by_id(self, walnut_id: str) -> Optional[WalnutDTO]:
        walnut_dao = self.walnut_reader.get_by_id(walnut_id)
        if walnut_dao is None:
            return None
        return self.walnut_mapper.dao_to_dto(walnut_dao)

    def get_all(self) -> List[WalnutDTO]:
        walnut_daos = self.walnut_reader.get_all()
        return [self.walnut_mapper.dao_to_dto(dao) for dao in walnut_daos]

    def load_from_filesystem(self, walnut_id: str) -> Optional[WalnutDTO]:
        image_root = Path(self.app_config.image_root)
        image_directory = image_root / walnut_id

        if not image_directory.exists():
            return None

        walnut_file_dao = WalnutImageLoader.load_walnut_from_directory(
            walnut_id, image_directory
        )
        if walnut_file_dao is None:
            return None

        return self.walnut_mapper.file_dao_to_dto(walnut_file_dao, walnut_id)
