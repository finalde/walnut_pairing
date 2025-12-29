# application_layer/commands/command_objects/base_command.py
from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ICommand(ABC):
    timestamp: Optional[datetime] = None
    user_id: Optional[str] = None
