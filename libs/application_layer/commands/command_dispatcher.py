# application_layer/commands/command_dispatcher.py
from abc import ABC, abstractmethod
from typing import Dict, Type, Any
from datetime import datetime

from .command_objects.base__command import ICommand
from .command_handlers.base__command_handler import ICommandHandler


class ICommandDispatcher(ABC):
    @abstractmethod
    def dispatch(self, command: ICommand) -> None:
        pass

    @abstractmethod
    def register_handler(self, command_type: Type[ICommand], handler: ICommandHandler) -> None:
        pass


class CommandDispatcher(ICommandDispatcher):
    def __init__(self) -> None:
        self._handlers: Dict[Type[ICommand], ICommandHandler] = {}

    def dispatch(self, command: ICommand) -> None:
        if command.timestamp is None:
            command.timestamp = datetime.now()

        command_type = type(command)
        handler = self._handlers.get(command_type)
        if handler is None:
            raise ValueError(f"No handler registered for command type: {command_type.__name__}")

        handler.handle(command)

    def register_handler(self, command_type: Type[ICommand], handler: ICommandHandler) -> None:
        self._handlers[command_type] = handler
    
    @classmethod
    def create_with_handlers(cls, walnut_writer: Any) -> "CommandDispatcher":
        from .command_handlers.walnut__command_handler import (
            CreateFakeWalnutHandler,
        )
        from .command_objects.walnut__command import (
            CreateFakeWalnutCommand,
        )
        
        dispatcher = cls()
        create_fake_handler = CreateFakeWalnutHandler(
            walnut_writer=walnut_writer,
        )
        dispatcher.register_handler(CreateFakeWalnutCommand, create_fake_handler)
        return dispatcher
