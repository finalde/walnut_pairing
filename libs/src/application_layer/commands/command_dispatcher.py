# src/application_layer/commands/command_dispatcher.py
from abc import ABC, abstractmethod
from typing import Dict, Type, Optional
from enum import Enum
import uuid
from datetime import datetime
from queue import Queue
import threading

from .command_objects.base_command import ICommand
from .command_handlers.base_handler import ICommandHandler


class ExecutionMode(Enum):
    SYNC = "sync"
    ASYNC = "async"


class ICommandDispatcher(ABC):
    @abstractmethod
    def dispatch(self, command: ICommand) -> None:
        pass

    @abstractmethod
    def register_handler(self, command_type: Type[ICommand], handler: ICommandHandler) -> None:
        pass


class SyncCommandDispatcher(ICommandDispatcher):
    def __init__(self) -> None:
        self._handlers: Dict[Type[ICommand], ICommandHandler] = {}

    def dispatch(self, command: ICommand) -> None:
        if command.command_id is None:
            command.command_id = str(uuid.uuid4())
        if command.timestamp is None:
            command.timestamp = datetime.now()

        command_type = type(command)
        handler = self._handlers.get(command_type)
        if handler is None:
            raise ValueError(f"No handler registered for command type: {command_type.__name__}")

        handler.handle(command)

    def register_handler(self, command_type: Type[ICommand], handler: ICommandHandler) -> None:
        self._handlers[command_type] = handler


class AsyncCommandDispatcher(ICommandDispatcher):
    def __init__(self) -> None:
        self._handlers: Dict[Type[ICommand], ICommandHandler] = {}
        self._queue: Queue[ICommand] = Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._running: bool = False
        self._start_worker()

    def _start_worker(self) -> None:
        self._running = True
        self._worker_thread = threading.Thread(target=self._process_commands, daemon=True)
        self._worker_thread.start()

    def _process_commands(self) -> None:
        while self._running:
            try:
                command = self._queue.get(timeout=1.0)
                command_type = type(command)
                handler = self._handlers.get(command_type)
                if handler:
                    try:
                        handler.handle(command)
                    except Exception as e:
                        print(f"Error handling command {command.command_id}: {e}")
                self._queue.task_done()
            except Exception:
                continue

    def dispatch(self, command: ICommand) -> None:
        if command.command_id is None:
            command.command_id = str(uuid.uuid4())
        if command.timestamp is None:
            command.timestamp = datetime.now()

        self._queue.put(command)

    def register_handler(self, command_type: Type[ICommand], handler: ICommandHandler) -> None:
        self._handlers[command_type] = handler

    def stop(self) -> None:
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)
        self._queue.join()


class CommandDispatcher(ICommandDispatcher):
    def __init__(
        self,
        sync_dispatcher: SyncCommandDispatcher,
        async_dispatcher: AsyncCommandDispatcher,
        command_config: Dict[Type[ICommand], ExecutionMode],
    ) -> None:
        self._sync_dispatcher: SyncCommandDispatcher = sync_dispatcher
        self._async_dispatcher: AsyncCommandDispatcher = async_dispatcher
        self._command_config: Dict[Type[ICommand], ExecutionMode] = command_config

    def dispatch(self, command: ICommand) -> None:
        command_type = type(command)
        mode = self._command_config.get(command_type, ExecutionMode.SYNC)
        
        if mode == ExecutionMode.SYNC:
            self._sync_dispatcher.dispatch(command)
        else:
            self._async_dispatcher.dispatch(command)

    def register_handler(self, command_type: Type[ICommand], handler: ICommandHandler) -> None:
        self._sync_dispatcher.register_handler(command_type, handler)
        self._async_dispatcher.register_handler(command_type, handler)
