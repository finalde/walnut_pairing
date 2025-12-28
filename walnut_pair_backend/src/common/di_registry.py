# src/common/di_registry.py
"""
Dependency Injection Registry - Maps interfaces to implementations.
Just register once, and dependencies are automatically resolved.
"""
from typing import Dict, Type, TypeVar, Any
from src.common.interfaces import IAppConfig, IDatabaseConnection
from src.common.app_config import AppConfig
from src.domain_layers.services.embedding_service import (
    IImageEmbeddingService,
    ImageEmbeddingService,
)
from src.data_access_layers.db_readers import (
    IWalnutReader,
    WalnutReader,
    IWalnutImageReader,
    WalnutImageReader,
    IWalnutImageEmbeddingReader,
    WalnutImageEmbeddingReader,
)
from src.data_access_layers.db_writers import (
    IWalnutWriter,
    WalnutWriter,
    IWalnutImageWriter,
    WalnutImageWriter,
    IWalnutImageEmbeddingWriter,
    WalnutImageEmbeddingWriter,
)
from src.business_layers.walnut_bl import IWalnutBL, WalnutBL
from src.application.application import IApplication, Application

T = TypeVar("T")


class DIRegistry:
    """Registry that maps interfaces to their implementations."""

    _registry: Dict[Type[Any], Type[Any]] = {}

    @classmethod
    def register(cls, interface: Type[T], implementation: Type[T]) -> None:
        """
        Register an interface-to-implementation mapping.

        Args:
            interface: The interface/abstract class
            implementation: The concrete implementation class
        """
        cls._registry[interface] = implementation

    @classmethod
    def get(cls, interface: Type[T]) -> Type[T]:
        """
        Get the implementation for an interface.

        Args:
            interface: The interface to look up

        Returns:
            The registered implementation class

        Raises:
            KeyError: If the interface is not registered
        """
        if interface not in cls._registry:
            raise KeyError(
                f"Interface {interface.__name__} is not registered. "
                f"Register it using DIRegistry.register({interface.__name__}, ImplementationClass)"
            )
        return cls._registry[interface]

    @classmethod
    def is_registered(cls, interface: Type[Any]) -> bool:
        """Check if an interface is registered."""
        return interface in cls._registry


# Register all interface-to-implementation mappings
# Add new mappings here when you create new interfaces
DIRegistry.register(IAppConfig, AppConfig)
DIRegistry.register(IImageEmbeddingService, ImageEmbeddingService)
DIRegistry.register(IWalnutImageEmbeddingReader, WalnutImageEmbeddingReader)
DIRegistry.register(IWalnutImageReader, WalnutImageReader)
DIRegistry.register(IWalnutReader, WalnutReader)
DIRegistry.register(IWalnutImageEmbeddingWriter, WalnutImageEmbeddingWriter)
DIRegistry.register(IWalnutImageWriter, WalnutImageWriter)
DIRegistry.register(IWalnutWriter, WalnutWriter)
DIRegistry.register(IWalnutBL, WalnutBL)
DIRegistry.register(IApplication, Application)

# Note: IDatabaseConnection is handled specially via factory function
# since it requires AppConfig to create

