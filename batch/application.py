# batch/application.py
from pathlib import Path
from typing import Optional

from application_layer.commands.command_dispatcher import ICommandDispatcher
from application_layer.commands.command_objects.walnut__command import (
    CreateWalnutFromImagesCommand,
)
from application_layer.queries.walnut__query import IWalnutQuery
from common.interfaces import IAppConfig
from common.logger import get_logger


class IApplication:
    pass


class Application:
    def __init__(
        self,
        command_dispatcher: ICommandDispatcher,
        walnut_query: IWalnutQuery,
        app_config: IAppConfig,
    ) -> None:
        self.command_dispatcher: ICommandDispatcher = command_dispatcher
        self.walnut_query: IWalnutQuery = walnut_query
        self.app_config: IAppConfig = app_config
        self.logger = get_logger(__name__)

    def run(self) -> None:
        image_root = Path(self.app_config.image_root)
        if not image_root.exists():
            self.logger.error("image_root_not_found", image_root=str(image_root))
            return

        self.logger.info("scanning_images_directory", image_root=str(image_root))

        walnut_directories = sorted([d for d in image_root.iterdir() if d.is_dir()])
        if not walnut_directories:
            self.logger.warning("no_walnut_directories_found", image_root=str(image_root))
            return

        self.logger.info("walnut_directories_found", count=len(walnut_directories))

        for walnut_dir in walnut_directories:
            walnut_id = walnut_dir.name
            self.logger.info("processing_walnut", walnut_id=walnut_id, directory=str(walnut_dir))

            try:
                command = CreateWalnutFromImagesCommand(
                    walnut_id=walnut_id,
                    description=f"Walnut {walnut_id} loaded from images directory",
                    save_intermediate_results=True,
                )
                self.command_dispatcher.dispatch(command)

                saved_walnut = self.walnut_query.get_by_id(walnut_id)
                if saved_walnut:
                    self.logger.info(
                        "walnut_processed_successfully",
                        walnut_id=saved_walnut.walnut_id,
                        image_count=len(saved_walnut.images),
                        length_mm=saved_walnut.length_mm,
                        width_mm=saved_walnut.width_mm,
                        height_mm=saved_walnut.height_mm,
                    )
                else:
                    self.logger.warning("walnut_not_found_after_processing", walnut_id=walnut_id)
            except Exception as e:
                self.logger.error(
                    "walnut_processing_error",
                    walnut_id=walnut_id,
                    error=str(e),
                    exc_info=True,
                )

        all_walnuts = self.walnut_query.get_all()
        self.logger.info("processing_complete", total_walnuts=len(all_walnuts))
