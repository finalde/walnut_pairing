# batch/application.py
from ast import List
from pathlib import Path

from application_layer.commands.command_dispatcher import ICommandDispatcher
from application_layer.commands.command_objects.walnut__command import (
    CompareWalnutsCommand,
    CreateWalnutFromImagesCommand,
)
from application_layer.queries.walnut__query import IWalnutQuery
from common.enums import ComparisonModeEnum
from common.interfaces import IAppConfig
from common.logger import get_logger
from domain_layer.entities.walnut__entity import WalnutEntity


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
        processed_count = 0
        
        for walnut_dir in walnut_directories:
            walnut_id = walnut_dir.name
            
            # Check if walnut already exists in database
            existing_walnut = self.walnut_query.get_by_id(walnut_id)
            if existing_walnut:
                self.logger.debug(
                    "walnut_already_processed",
                    walnut_id=walnut_id,
                    note="Skipping - already in database",
                )
                continue

            self.logger.info("processing_walnut", walnut_id=walnut_id, directory=str(walnut_dir))

            command = CreateWalnutFromImagesCommand(
                walnut_id=walnut_id,
                description=f"Walnut {walnut_id} loaded from images directory",
                save_intermediate_results=True,
            )
            self.command_dispatcher.dispatch(command)

            saved_walnut = self.walnut_query.get_by_id(walnut_id)
            processed_count += 1
            self.logger.info(
                "walnut_processed_successfully",
                walnut_id=saved_walnut.walnut_id,
                image_count=len(saved_walnut.images),
                width_mm=saved_walnut.width_mm,
                height_mm=saved_walnut.height_mm,
                thickness_mm=saved_walnut.thickness_mm,
            )

        self.logger.info("starting_walnut_comparison", note="Checking and creating comparisons for all walnuts")
   
        walnuts: List[WalnutEntity] = self.walnut_query.get_all_entities()
        walnut_ids = [walnut.id for walnut in walnuts]
        
        algorithm = self.app_config.algorithm
        compare_command = CompareWalnutsCommand(
            walnut_ids=walnut_ids,
            comparison_mode=algorithm.comparison_mode_enum,
            # Basic similarity weights
            width_weight=algorithm.basic.width_weight,
            height_weight=algorithm.basic.height_weight,
            thickness_weight=algorithm.basic.thickness_weight,
            # Advanced similarity weights
            front_weight=algorithm.advanced.front_weight,
            back_weight=algorithm.advanced.back_weight,
            left_weight=algorithm.advanced.left_weight,
            right_weight=algorithm.advanced.right_weight,
            top_weight=algorithm.advanced.top_weight,
            down_weight=algorithm.advanced.down_weight,
            # Final similarity weights
            basic_weight=algorithm.final.basic_weight,
            advanced_weight=algorithm.final.advanced_weight,
            # Threshold
            skip_advanced_threshold=algorithm.basic.skip_advanced_threshold,
            # Discriminative parameters
            discriminative_power=algorithm.advanced.discriminative_power,
            min_expected_cosine=algorithm.advanced.min_expected_cosine,
            max_expected_cosine=algorithm.advanced.max_expected_cosine,
        )
        self.command_dispatcher.dispatch(compare_command)
