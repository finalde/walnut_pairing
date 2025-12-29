# common/di_registry.py
from typing import Dict, Type, TypeVar, Any
from common.interfaces import IAppConfig
from domain_layer.services.embedding__service import (
    IImageEmbeddingService,
    ImageEmbeddingService,
)
from infrastructure_layer.db_readers import (
    IWalnutDBReader,
    WalnutDBReader,
    IWalnutImageEmbeddingDBReader,
    WalnutImageEmbeddingDBReader,
)
from infrastructure_layer.file_readers import (
    IWalnutImageFileReader,
    WalnutImageFileReader,
)
from infrastructure_layer.db_writers import (
    IWalnutDBWriter,
    WalnutDBWriter,
    IWalnutImageDBWriter,
    WalnutImageDBWriter,
    IWalnutImageEmbeddingDBWriter,
    WalnutImageEmbeddingDBWriter,
)
from application_layer.walnut__al import IWalnutAL, WalnutAL
from application_layer.mappers.walnut__mapper import IWalnutMapper, WalnutMapper
from application_layer.queries.walnut__query import WalnutQuery

T = TypeVar("T")


class DIRegistry:
    _registry: Dict[Type[Any], Type[Any]] = {}

    @classmethod
    def register(cls, interface: Type[T], implementation: Type[T]) -> None:
        cls._registry[interface] = implementation

    @classmethod
    def get(cls, interface: Type[T]) -> Type[T]:
        if interface not in cls._registry:
            raise KeyError(
                f"Interface {interface.__name__} is not registered. "
                f"Register it using DIRegistry.register({interface.__name__}, ImplementationClass)"
            )
        return cls._registry[interface]

    @classmethod
    def is_registered(cls, interface: Type[Any]) -> bool:
        return interface in cls._registry


try:
    from batch.app_config import AppConfig
    DIRegistry.register(IAppConfig, AppConfig)
except ImportError:
    pass
DIRegistry.register(IImageEmbeddingService, ImageEmbeddingService)
DIRegistry.register(IWalnutImageEmbeddingDBReader, WalnutImageEmbeddingDBReader)
DIRegistry.register(IWalnutImageFileReader, WalnutImageFileReader)
DIRegistry.register(IWalnutDBReader, WalnutDBReader)
DIRegistry.register(IWalnutImageEmbeddingDBWriter, WalnutImageEmbeddingDBWriter)
DIRegistry.register(IWalnutImageDBWriter, WalnutImageDBWriter)
DIRegistry.register(IWalnutDBWriter, WalnutDBWriter)
DIRegistry.register(IWalnutAL, WalnutAL)
DIRegistry.register(IWalnutMapper, WalnutMapper)
DIRegistry.register(WalnutQuery, WalnutQuery)
