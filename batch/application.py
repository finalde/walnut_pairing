# batch/application.py
from application_layer.commands.command_dispatcher import ICommandDispatcher
from application_layer.queries.walnut__query import IWalnutQuery
from application_layer.commands.command_objects.walnut__command import (
    CreateFakeWalnutCommand,
)
from common.logger import get_logger


class IApplication:
    pass


class Application:
    def __init__(
        self,
        command_dispatcher: ICommandDispatcher,
        walnut_query: IWalnutQuery,
    ) -> None:
        self.command_dispatcher: ICommandDispatcher = command_dispatcher
        self.walnut_query: IWalnutQuery = walnut_query
        self.logger = get_logger(__name__)

    def run(self) -> None:
        command = CreateFakeWalnutCommand(walnut_id="WALNUT-TEST-001")
        self.command_dispatcher.dispatch(command)
        
        fake_walnut = self.walnut_query.get_by_id("WALNUT-TEST-001")
        if fake_walnut:
            self.logger.info(
                "walnut_found",
                walnut_id=fake_walnut.walnut_id,
                image_count=len(fake_walnut.images),
            )
            for img in fake_walnut.images:
                self.logger.debug(
                    "walnut_image",
                    walnut_id=fake_walnut.walnut_id,
                    side=img.side,
                    image_id=img.image_id,
                    embedding_id=img.embedding_id,
                )

        self.logger.info("testing_filesystem_load", walnut_id="0001")
        try:
            loaded_walnut = self.walnut_query.load_from_filesystem("0001")
            if loaded_walnut:
                self.logger.info(
                    "walnut_loaded_from_filesystem",
                    walnut_id=loaded_walnut.walnut_id,
                    image_count=len(loaded_walnut.images),
                )
                for img in loaded_walnut.images:
                    self.logger.debug(
                        "filesystem_image",
                        walnut_id=loaded_walnut.walnut_id,
                        side=img.side,
                        image_path=img.image_path,
                        width=img.width,
                        height=img.height,
                    )
            else:
                self.logger.warning("walnut_not_found_in_filesystem", walnut_id="0001")
        except Exception as e:
            self.logger.error(
                "filesystem_load_error",
                walnut_id="0001",
                error=str(e),
                exc_info=True,
            )

        all_walnuts = self.walnut_query.get_all()
        self.logger.info("all_walnuts_queried", count=len(all_walnuts))
