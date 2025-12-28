# src/application_layer/commands/command_objects/walnut_command.py
from dataclasses import dataclass
from typing import Optional

from .base_command import ICommand


@dataclass
class CreateFakeWalnutCommand(ICommand):
    walnut_id: str = ""
    description: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.walnut_id:
            raise ValueError("walnut_id is required")
