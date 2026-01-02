# ============================================================
# Batch-specific DI Registry Registrations
# ============================================================
# This module registers batch-specific interface-to-implementation
# mappings. The DIRegistry class itself is defined in common.di_registry.
# ============================================================

from application_layer.mappers.walnut__mapper import IWalnutMapper, WalnutMapper
from application_layer.mappers.walnut_comparison__mapper import IWalnutComparisonMapper, WalnutComparisonMapper
from application_layer.queries import IWalnutQuery, WalnutQuery
from application_layer.walnut__al import IWalnutAL, WalnutAL
from common.di_registry import DIRegistry
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
    IWalnutComparisonDBWriter,
    IWalnutDBWriter,
    IWalnutImageDBWriter,
    IWalnutImageEmbeddingDBWriter,
    WalnutComparisonDBWriter,
    WalnutDBWriter,
    WalnutImageDBWriter,
    WalnutImageEmbeddingDBWriter,
)
from infrastructure_layer.file_readers import (
    IWalnutImageFileReader,
    WalnutImageFileReader,
)
from infrastructure_layer.services import (
    IImageObjectFinder,
    ImageObjectFinder,
)

from batch.app_config import AppConfig


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
DIRegistry.register(IImageObjectFinder, ImageObjectFinder)
DIRegistry.register(IWalnutComparisonDBWriter, WalnutComparisonDBWriter)
DIRegistry.register(IWalnutComparisonMapper, WalnutComparisonMapper)
