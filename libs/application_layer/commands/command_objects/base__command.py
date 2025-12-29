# application_layer/commands/command_objects/base_command.py
from abc import ABC
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class ICommand(ABC):
    timestamp: Optional[datetime] = None
    user_id: Optional[str] = None
