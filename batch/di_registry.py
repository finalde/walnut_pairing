# batch/di_registry.py
from typing import Any, Dict, Type, TypeVar

from application_layer.mappers.walnut__mapper import IWalnutMapper, WalnutMapper
from application_layer.queries import IWalnutQuery, WalnutQuery
from application_layer.walnut__al import IWalnutAL, WalnutAL
from common.interfaces import IAppConfig
from infrastructure_layer.db_readers import (
    IWalnutDBReader,
    IWalnutImageDBReader,
    IWalnutImageEmbeddingDBReader,
    WalnutDBReader,
    WalnutImageDBReader,
    WalnutImageEmbeddingDBReader,
)
from infrastructure_layer.db_writers import (
    IWalnutDBWriter,
    IWalnutImageDBWriter,
    IWalnutImageEmbeddingDBWriter,
    WalnutDBWriter,
    WalnutImageDBWriter,
    WalnutImageEmbeddingDBWriter,
)
from infrastructure_layer.file_readers import (
    IWalnutImageFileReader,
    WalnutImageFileReader,
)
from infrastructure_layer.services import IWalnutImageService, WalnutImageService
from infrastructure_layer.services.walnut_image_service import (
    IContourFinder,
    IDimensionMeasurer,
    IImageSegmenter,
    ContourFinder,
    DimensionMeasurer,
    ImageSegmenter,
)

from batch.app_config import AppConfig

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


DIRegistry.register(IAppConfig, AppConfig)
DIRegistry.register(IWalnutImageEmbeddingDBReader, WalnutImageEmbeddingDBReader)
DIRegistry.register(IWalnutImageDBReader, WalnutImageDBReader)
DIRegistry.register(IWalnutImageFileReader, WalnutImageFileReader)
DIRegistry.register(IWalnutDBReader, WalnutDBReader)
DIRegistry.register(IWalnutImageEmbeddingDBWriter, WalnutImageEmbeddingDBWriter)
DIRegistry.register(IWalnutImageDBWriter, WalnutImageDBWriter)
DIRegistry.register(IWalnutDBWriter, WalnutDBWriter)
DIRegistry.register(IWalnutAL, WalnutAL)
DIRegistry.register(IWalnutMapper, WalnutMapper)
DIRegistry.register(IWalnutQuery, WalnutQuery)
DIRegistry.register(IImageSegmenter, ImageSegmenter)
DIRegistry.register(IContourFinder, ContourFinder)
DIRegistry.register(IDimensionMeasurer, DimensionMeasurer)
DIRegistry.register(IWalnutImageService, WalnutImageService)
