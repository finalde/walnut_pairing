# batch/main.py
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
print(f"project_root: {project_root}")
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "libs"))

from batch.application import IApplication, Application
from batch.di_container import Container
from src.application_layer.commands.command_dispatcher import (
    SyncCommandDispatcher,
    AsyncCommandDispatcher,
    CommandDispatcher,
    ExecutionMode,
)
from src.application_layer.commands.command_handlers.walnut_command_handler import (
    CreateFakeWalnutHandler,
)
from src.application_layer.commands.command_objects.walnut_command import (
    CreateFakeWalnutCommand,
)


def main() -> None:
    config_path = project_root / "batch/config.yml"
    
    container = Container()
    container.config_path.from_value(str(config_path))
    
    command_dispatcher = SyncCommandDispatcher()
    create_fake_handler = CreateFakeWalnutHandler(
        walnut_writer=container.walnutdbwriter(),
    )
    command_dispatcher.register_handler(CreateFakeWalnutCommand, create_fake_handler)
    
    dispatcher = CommandDispatcher(
        sync_dispatcher=command_dispatcher,
        async_dispatcher=AsyncCommandDispatcher(),
        command_config={CreateFakeWalnutCommand: ExecutionMode.SYNC},
    )
    
    app: IApplication = Application(
        command_dispatcher=dispatcher,
        walnut_query=container.walnutquery(),
    )
    app.run()


if __name__ == "__main__":
    main()
