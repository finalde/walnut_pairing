# ============================================================
# Common DI Registry
# ============================================================
# This module provides a generic interface-to-implementation
# registry that can be shared between batch and webapi applications.
# ============================================================

from abc import ABC
from dataclasses import dataclass
from typing import Dict, Optional, Type, TypeVar

# TypeVar bound to ABC to ensure interface constraint
TInterface = TypeVar("TInterface", bound=ABC)
# TypeVar for implementation that must be a subclass of the interface
TImplementation = TypeVar("TImplementation")


# Scope constants
class Scope:
    """Dependency injection scope types."""
    SINGLETON = "singleton"  # Single instance for all requests
    REQUEST = "request"  # One instance per request
    TRANSIENT = "transient"  # New instance each time


@dataclass
class Registration:
    """Registration information for an interface."""
    implementation: Type[TImplementation]
    scope: str = Scope.REQUEST  # Default to request scope


class DIRegistry:
    """
    Generic interface-to-implementation registry with scope support.
    
    This registry allows applications to register interface/implementation
    pairs with scope information without coupling to specific DI frameworks.
    The actual provider creation happens in the DI container using this registry.
    
    Usage:
        DIRegistry.register(IMyInterface, MyImplementation, Scope.SINGLETON)
        impl = DIRegistry.get(IMyInterface)
        scope = DIRegistry.get_scope(IMyInterface)
    """
    
    _registry: Dict[Type[TInterface], Registration] = {}

    @classmethod
    def register(
        cls,
        interface: Type[TInterface],
        implementation: Type[TImplementation],
        scope: str = Scope.REQUEST,
    ) -> None:
        """
        Register an interface with its implementation and scope.
        
        Args:
            interface: The interface (ABC) type to register
            implementation: The implementation class that must implement the interface
            scope: The scope for the dependency (Scope.SINGLETON, Scope.REQUEST, or Scope.TRANSIENT)
            
        Raises:
            TypeError: If interface is not an ABC or implementation doesn't implement the interface
            ValueError: If scope is invalid
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
        
        # Validate scope
        valid_scopes = [Scope.SINGLETON, Scope.REQUEST, Scope.TRANSIENT]
        if scope not in valid_scopes:
            raise ValueError(
                f"Invalid scope '{scope}'. Must be one of: {valid_scopes}"
            )
        
        cls._registry[interface] = Registration(implementation=implementation, scope=scope)

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
                f"Register it using DIRegistry.register({interface.__name__}, ImplementationClass, scope)"
            )
        return cls._registry[interface].implementation
    
    @classmethod
    def get_scope(cls, interface: Type[TInterface]) -> str:
        """
        Get the scope for an interface.
        
        Args:
            interface: The interface type to look up
            
        Returns:
            The scope string (Scope.SINGLETON, Scope.REQUEST, or Scope.TRANSIENT)
            
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
                f"Register it using DIRegistry.register({interface.__name__}, ImplementationClass, scope)"
            )
        return cls._registry[interface].scope
    
    @classmethod
    def get_registration(cls, interface: Type[TInterface]) -> Registration:
        """
        Get the full registration information for an interface.
        
        Args:
            interface: The interface type to look up
            
        Returns:
            Registration object containing implementation and scope
            
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
                f"Register it using DIRegistry.register({interface.__name__}, ImplementationClass, scope)"
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
