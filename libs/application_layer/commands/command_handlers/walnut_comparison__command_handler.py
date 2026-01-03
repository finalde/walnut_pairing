# application_layer/commands/command_handlers/walnut_comparison__command_handler.py
from typing import List

from application_layer.commands.command_objects.walnut__command import CompareWalnutsCommand
from application_layer.commands.command_handlers.base__command_handler import ICommandHandler
from application_layer.mappers.walnut_comparison__mapper import IWalnutComparisonMapper
from application_layer.queries.walnut__query import IWalnutQuery
from common.constants import SYSTEM_USER
from common.logger import get_logger
from domain_layer.entities.walnut_comparison__entity import WalnutComparisonEntity
from infrastructure_layer.db_writers.walnut_comparison__db_writer import IWalnutComparisonDBWriter


class CompareWalnutsHandler(ICommandHandler[CompareWalnutsCommand]):
    """Command handler for comparing walnuts and calculating similarity scores."""

    def __init__(
        self,
        walnut_query: IWalnutQuery,
        walnut_comparison_writer: IWalnutComparisonDBWriter,
        walnut_comparison_mapper: IWalnutComparisonMapper,
    ) -> None:
        self.walnut_query: IWalnutQuery = walnut_query
        self.walnut_comparison_writer: IWalnutComparisonDBWriter = walnut_comparison_writer
        self.walnut_comparison_mapper: IWalnutComparisonMapper = walnut_comparison_mapper
        self.logger = get_logger(__name__)

    async def handle_async(self, command: CompareWalnutsCommand) -> None:
        """
        Compare walnuts and calculate similarity scores.
        
        Orchestration:
        1. Get walnut entities (by IDs if specified, or all)
        2. Create comparison entity (domain validation happens here)
        3. Execute comparison (domain logic)
        4. Map all results to DAOs
        5. Bulk save to database
        """
        # Get walnut entities
        if command.walnut_ids:
            walnut_entities = await self.walnut_query.get_entities_by_ids_async(command.walnut_ids)
        else:
            walnut_entities = await self.walnut_query.get_all_entities_async()

        self.logger.info(
            "starting_walnut_comparison",
            total_walnuts=len(walnut_entities),
            walnut_ids=command.walnut_ids if command.walnut_ids else None,
            comparison_mode=command.comparison_mode.value,
        )

        # Create comparison entity (domain validation happens here - will return error if < 2 walnuts)
        comparison_entity_result = WalnutComparisonEntity.create(
            walnuts=walnut_entities,
            comparison_mode=command.comparison_mode,
            width_weight=command.width_weight,
            height_weight=command.height_weight,
            thickness_weight=command.thickness_weight,
            front_weight=command.front_weight,
            back_weight=command.back_weight,
            left_weight=command.left_weight,
            right_weight=command.right_weight,
            top_weight=command.top_weight,
            down_weight=command.down_weight,
            basic_weight=command.basic_weight,
            advanced_weight=command.advanced_weight,
            skip_advanced_threshold=command.skip_advanced_threshold,
            discriminative_power=command.discriminative_power,
            min_expected_cosine=command.min_expected_cosine,
            max_expected_cosine=command.max_expected_cosine,
        )
        if comparison_entity_result.is_left():
            error = comparison_entity_result.value
            self.logger.error(
                "comparison_entity_creation_failed",
                error=str(error),
            )
            return

        comparison_entity: WalnutComparisonEntity = comparison_entity_result.value

        # Execute comparison (domain logic)
        comparison_vos: List = comparison_entity.compare_all()

        # Map all value objects to DAOs
        comparison_daos = self.walnut_comparison_mapper.value_objects_to_daos(
            comparison_vos=comparison_vos,
            created_by=SYSTEM_USER,
            updated_by=SYSTEM_USER,
        )

        # Bulk save to database
        try:
            saved_comparisons = await self.walnut_comparison_writer.bulk_save_or_update_async(comparison_daos)

            self.logger.info(
                "walnut_comparison_complete",
                total_comparisons=len(saved_comparisons),
                expected_pairs=len(walnut_entities) * (len(walnut_entities) - 1) // 2,
            )
        except Exception as e:
            self.logger.error(
                "bulk_save_error",
                error=str(e),
                comparison_count=len(comparison_daos),
                exc_info=True,
            )
            raise

