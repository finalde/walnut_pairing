# ============================================================
# Common DI Registry
# ============================================================
# This module provides a generic interface-to-implementation
# registry that can be shared between batch and webapi applications.
# ============================================================

from abc import ABC
from typing import Dict, Type, TypeVar

# TypeVar bound to ABC to ensure interface constraint
TInterface = TypeVar("TInterface", bound=ABC)
# TypeVar for implementation that must be a subclass of the interface
TImplementation = TypeVar("TImplementation")


class DIRegistry:
    """
    Generic interface-to-implementation registry.
    
    This registry allows applications to register interface/implementation
    pairs without coupling to specific DI frameworks. The actual provider
    creation happens in the DI container using this registry.
    
    Usage:
        DIRegistry.register(IMyInterface, MyImplementation)
        impl = DIRegistry.get(IMyInterface)
    """
    
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
