# src/application_layer/commands/command_handlers/base_handler.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ..command_objects.base_command import ICommand

TCommand = TypeVar("TCommand", bound=ICommand)


class ICommandHandler(ABC, Generic[TCommand]):
    @abstractmethod
    def handle(self, command: TCommand) -> None:
        pass
