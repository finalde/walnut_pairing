# application_layer/commands/command_dispatcher.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Type

from common.interfaces import IDependencyProvider

from .command_handlers.base__command_handler import ICommandHandler
from .command_objects.base__command import ICommand
from .command_handlers.walnut__command_handler import (
    CreateWalnutFromImagesHandler,
)
from .command_handlers.walnut_comparison__command_handler import (
    CompareWalnutsHandler,
)
from .command_objects.walnut__command import (
    CompareWalnutsCommand,
    CreateWalnutFromImagesCommand,
)

class ICommandDispatcher(ABC):
    @abstractmethod
    async def dispatch_async(self, command: ICommand) -> None:
        pass

    @abstractmethod
    def register_handler(self, command_type: Type[ICommand], handler: ICommandHandler) -> None:
        pass


class CommandDispatcher(ICommandDispatcher):
    def __init__(self) -> None:
        self._handlers: Dict[Type[ICommand], ICommandHandler] = {}

    async def dispatch_async(self, command: ICommand) -> None:
        if command.timestamp is None:
            command.timestamp = datetime.now()

        command_type = type(command)
        handler = self._handlers.get(command_type)
        if handler is None:
            raise ValueError(f"No handler registered for command type: {command_type.__name__}")

        await handler.handle_async(command)

    def register_handler(self, command_type: Type[ICommand], handler: ICommandHandler) -> None:
        self._handlers[command_type] = handler

    @classmethod
    def create_with_handlers(cls, dependency_provider: IDependencyProvider) -> "CommandDispatcher":
        dispatcher = cls()

        create_from_images_handler = dependency_provider.resolve(CreateWalnutFromImagesHandler)
        dispatcher.register_handler(CreateWalnutFromImagesCommand, create_from_images_handler)

        compare_walnuts_handler = dependency_provider.resolve(CompareWalnutsHandler)
        dispatcher.register_handler(CompareWalnutsCommand, compare_walnuts_handler)

        return dispatcher
