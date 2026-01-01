# application_layer/queries/walnut__query.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from application_layer.dtos.walnut__dto import WalnutDTO
from application_layer.mappers.walnut__mapper import IWalnutMapper
from common.interfaces import IAppConfig
from infrastructure_layer.db_readers import IWalnutDBReader
from infrastructure_layer.file_readers.walnut_image__file_reader import IWalnutImageFileReader

if TYPE_CHECKING:
    from domain_layer.entities.walnut__entity import WalnutEntity


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

    @abstractmethod
    def get_entities_by_ids(self, walnut_ids: List[str]) -> List["WalnutEntity"]:
        """
        Get walnut entities by IDs.
        
        Returns list of WalnutEntity objects for the given IDs.
        Only returns entities that have valid dimensions.
        """
        pass

    @abstractmethod
    def get_all_entities(self) -> List["WalnutEntity"]:
        """
        Get all walnut entities from the database.
        
        Returns list of WalnutEntity objects.
        Only returns entities that have valid dimensions.
        """
        pass


class WalnutQuery(IWalnutQuery):
    def __init__(
        self,
        walnut_reader: IWalnutDBReader,
        walnut_mapper: IWalnutMapper,
        app_config: IAppConfig,
        walnut_image_file_reader: IWalnutImageFileReader,
    ) -> None:
        self.walnut_reader: IWalnutDBReader = walnut_reader
        self.walnut_mapper: IWalnutMapper = walnut_mapper
        self.app_config: IAppConfig = app_config
        self.walnut_image_file_reader: IWalnutImageFileReader = walnut_image_file_reader

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

        walnut_file_dao = self.walnut_image_file_reader.load_walnut_from_directory(walnut_id, image_directory)
        if walnut_file_dao is None:
            return None

        return self.walnut_mapper.file_dao_to_dto(walnut_file_dao, walnut_id)

    def get_entities_by_ids(self, walnut_ids: List[str]) -> List["WalnutEntity"]:
        """
        Get walnut entities by IDs.
        
        Returns list of WalnutEntity objects for the given IDs.
        Only returns entities that have valid dimensions.
        """
        entities: List["WalnutEntity"] = []
        
        for walnut_id in walnut_ids:
            walnut_dao = self.walnut_reader.get_by_id(walnut_id)
            if walnut_dao is None:
                continue
            
            # Convert DAO to entity using mapper
            entity_result = self.walnut_mapper.dao_to_entity(walnut_dao)
            if entity_result.is_right():
                entity = entity_result.value
                # Only include entities with valid dimensions
                if entity.dimensions is not None:
                    entities.append(entity)
        
        return entities

    def get_all_entities(self) -> List["WalnutEntity"]:
        """
        Get all walnut entities from the database.
        
        Returns list of WalnutEntity objects.
        Only returns entities that have valid dimensions.
        """
        walnut_daos = self.walnut_reader.get_all()
        entities: List["WalnutEntity"] = []
        
        for walnut_dao in walnut_daos:
            # Convert DAO to entity using mapper
            entity_result = self.walnut_mapper.dao_to_entity(walnut_dao)
            if entity_result.is_right():
                entity = entity_result.value
                # Only include entities with valid dimensions
                if entity.dimensions is not None:
                    entities.append(entity)
        
        return entities
