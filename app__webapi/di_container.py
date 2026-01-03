# app__webapi/di_container.py
"""WebAPI dependency injection container with scope support."""
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Type

from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession

from application_layer.mappers.walnut_comparison__mapper import (
    IWalnutComparisonMapper,
    WalnutComparisonMapper,
)
from application_layer.queries.walnut_comparison__query import (
    IWalnutComparisonQuery,
    WalnutComparisonQuery,
)
from common.di_container import (
    DependencyProviderWrapper,
    _container_resolve,
    _create_provider,
    _normalize_attr_name,
    _resolve_type_hints,
)
from common.di_registry import DIRegistry, Scope
from common.interfaces import DatabaseConfig, IAppConfig
from infrastructure_layer.db_readers import (
    IWalnutComparisonDBReader,
    WalnutComparisonDBReader,
)
from infrastructure_layer.session_factory import SessionFactory

from app__webapi.app_config import WebAPIAppConfig

if TYPE_CHECKING:
    pass


def create_webapi_app_config(config_path: Path) -> IAppConfig:
    """Create WebAPI app config from YAML file."""
    return WebAPIAppConfig.load_from_yaml(config_path)


def _register_dependencies() -> None:
    """Register all dependencies with their scopes in DIRegistry."""
    # Register mappers as Singleton (stateless, can be shared)
    DIRegistry.register(IWalnutComparisonMapper, WalnutComparisonMapper, Scope.SINGLETON)
    
    # Register readers as Request-scoped (one per HTTP request)
    DIRegistry.register(IWalnutComparisonDBReader, WalnutComparisonDBReader, Scope.REQUEST)
    
    # Register queries as Request-scoped (one per HTTP request)
    DIRegistry.register(IWalnutComparisonQuery, WalnutComparisonQuery, Scope.REQUEST)


# Note: _register_dependencies() is called in bootstrap_webapi_container()
# to ensure it's called after all imports are complete


class WebAPIContainer(containers.DeclarativeContainer):
    """
    WebAPI application DI container with scope support.
    
    Scopes:
    - Singleton: Single instance shared across all requests
    - Request: One instance per HTTP request (using FastAPI dependency)
    - Transient: New instance created each time
    
    Dependencies are registered in DIRegistry with scopes using:
        DIRegistry.register(IInterface, Implementation, Scope.SINGLETON)
    
    Providers are automatically created from the registry in bootstrap_webapi_container().
    """

    # Configuration
    config_path = providers.Configuration()

    # Singleton providers (shared across all requests)
    app_config = providers.Singleton(
        create_webapi_app_config,
        config_path=config_path,
    )

    database_config = providers.Singleton(
        lambda app_config: app_config.database,
        app_config=app_config,
    )

    session_factory = providers.Singleton(
        SessionFactory,
        database_config=database_config,
    )

    # Request-scoped providers (one per request)
    # These are created per request using FastAPI's Depends
    session = providers.Factory(
        lambda session_factory: session_factory.create_session(),
        session_factory=session_factory,
    )


def bootstrap_webapi_container(config_path: Path) -> WebAPIContainer:
    """
    Bootstrap and return the WebAPI container.
    
    This function:
    1. Registers all dependencies with their scopes in DIRegistry
    2. Creates the container with base providers (app_config, session, etc.)
    3. Automatically creates providers from DIRegistry for registered interfaces
    4. Configures the container
    
    Dependencies registered with DIRegistry.register() will be automatically
    created as providers based on their registered scopes.
    """
    # Register dependencies first
    _register_dependencies()
    
    # Create container with base providers
    container = WebAPIContainer()
    
    # Create providers from DIRegistry and add them to container
    # We need to handle dependencies that are already in the container (like session)
    providers_map: Dict[Type[Any], providers.Provider] = {}
    
    # Map special types to container providers
    # AsyncSession is provided by container.session
    type_to_container_attr: Dict[Type[Any], str] = {
        AsyncSession: "session",
    }
    
    # Helper to resolve a dependency type to a provider
    def resolve_dep_provider(dep_type: Type[Any]) -> providers.Provider:
        """Resolve a dependency type to a provider, checking container first."""
        # Check if it's already in providers_map
        if dep_type in providers_map:
            return providers_map[dep_type]
        
        # Check if it's a special type mapped to a container attribute
        if dep_type in type_to_container_attr:
            attr_name = type_to_container_attr[dep_type]
            if hasattr(container, attr_name):
                provider = getattr(container, attr_name)
                if isinstance(provider, providers.Provider):
                    providers_map[dep_type] = provider
                    return provider
        
        # Check if it's a container attribute (by normalized name)
        attr_name = _normalize_attr_name(dep_type)
        if hasattr(container, attr_name):
            provider = getattr(container, attr_name)
            if isinstance(provider, providers.Provider):
                providers_map[dep_type] = provider
                return provider
        
        # Check if it's registered in DIRegistry
        if DIRegistry.is_registered(dep_type):
            registration = DIRegistry.get_registration(dep_type)
            visited: set[Type[Any]] = set()
            provider = _create_provider(
                dep_type,
                registration.implementation,
                providers_map,
                visited,
                registration.scope,
            )
            providers_map[dep_type] = provider
            return provider
        
        raise ValueError(f"Cannot resolve dependency: {dep_type.__name__}")
    
    # Create providers for all registered interfaces
    for interface in DIRegistry._registry.keys():
        attr_name = _normalize_attr_name(interface)
        # Check if provider already exists and is a valid provider
        if hasattr(container, attr_name):
            existing = getattr(container, attr_name)
            if isinstance(existing, providers.Provider):
                # Already exists as a provider, skip
                providers_map[interface] = existing
                continue
            
        registration = DIRegistry.get_registration(interface)
        
        # Create provider with dependency resolution
        visited: set[Type[Any]] = set()
        
        # Override dependency resolution to use resolve_dep_provider
        # We'll create a custom version that uses our resolver
        hints = _resolve_type_hints(registration.implementation.__init__)
        deps: Dict[str, providers.Provider] = {}
        
        for name, param_type in hints.items():
            if name in ("self", "return"):
                continue
            try:
                deps[name] = resolve_dep_provider(param_type)
            except ValueError:
                # Try to get from container by name
                dep_attr_name = _normalize_attr_name(param_type)
                if hasattr(container, dep_attr_name):
                    deps[name] = getattr(container, dep_attr_name)
        
        # Create provider based on scope
        if registration.scope == Scope.SINGLETON:
            provider = providers.Singleton(registration.implementation, **deps)
        else:  # REQUEST or TRANSIENT
            provider = providers.Factory(registration.implementation, **deps)
        
        # Add provider to container as attribute
        setattr(container, attr_name, provider)
        providers_map[interface] = provider
    
    # Configure container
    container.config_path.from_value(str(config_path))
    return container
