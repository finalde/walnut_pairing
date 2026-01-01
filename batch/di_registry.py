# batch/di_registry.py
from abc import ABC
from typing import Dict, Type, TypeVar

from application_layer.mappers.walnut__mapper import IWalnutMapper, WalnutMapper
from application_layer.mappers.walnut_comparison__mapper import IWalnutComparisonMapper, WalnutComparisonMapper
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

# TypeVar bound to ABC to ensure interface constraint
TInterface = TypeVar("TInterface", bound=ABC)
# TypeVar for implementation that must be a subclass of the interface
TImplementation = TypeVar("TImplementation")


class DIRegistry:
    _registry: Dict[Type[TInterface], Type[TImplementation]] = {}

    @classmethod
    def register(cls, interface: Type[TInterface], implementation: Type[TImplementation]) -> None:
        """
        Register an interface with its implementation.
        
        Args:
            interface: The interface (ABC) type to register
            implementation: The implementation class that must implement the interface
            
        Raises:
            TypeError: If interface is not an ABC or implementation doesn't implement the interface
        """
        # Runtime validation: ensure interface is an ABC
        if not issubclass(interface, ABC):
            raise TypeError(
                f"Interface {interface.__name__} must be an abstract base class (ABC). "
                f"Use 'from abc import ABC' and inherit from ABC."
            )
        
        # Runtime validation: ensure implementation is a subclass of interface
        if not issubclass(implementation, interface):
            raise TypeError(
                f"Implementation {implementation.__name__} must implement interface {interface.__name__}. "
                f"Ensure {implementation.__name__} inherits from {interface.__name__}."
            )
        
        cls._registry[interface] = implementation

    @classmethod
    def get(cls, interface: Type[TInterface]) -> Type[TImplementation]:
        """
        Get the implementation for an interface.
        
        Args:
            interface: The interface type to look up
            
        Returns:
            The implementation class for the interface
            
        Raises:
            KeyError: If interface is not registered
            TypeError: If interface is not an ABC
        """
        # Runtime validation: ensure interface is an ABC
        if not issubclass(interface, ABC):
            raise TypeError(
                f"Interface {interface.__name__} must be an abstract base class (ABC). "
                f"Use 'from abc import ABC' and inherit from ABC."
            )
        
        if interface not in cls._registry:
            raise KeyError(
                f"Interface {interface.__name__} is not registered. "
                f"Register it using DIRegistry.register({interface.__name__}, ImplementationClass)"
            )
        return cls._registry[interface]

    @classmethod
    def is_registered(cls, interface: Type[TInterface]) -> bool:
        """
        Check if an interface is registered.
        
        Args:
            interface: The interface type to check
            
        Returns:
            True if interface is registered, False otherwise
        """
        if not issubclass(interface, ABC):
            return False
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
DIRegistry.register(IImageObjectFinder, ImageObjectFinder)
DIRegistry.register(IWalnutComparisonDBWriter, WalnutComparisonDBWriter)
DIRegistry.register(IWalnutComparisonMapper, WalnutComparisonMapper)
