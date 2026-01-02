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

    def handle(self, command: CompareWalnutsCommand) -> None:
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
            walnut_entities = self.walnut_query.get_entities_by_ids(command.walnut_ids)
        else:
            walnut_entities = self.walnut_query.get_all_entities()

        self.logger.info(
            "starting_walnut_comparison",
            total_walnuts=len(walnut_entities),
            walnut_ids=command.walnut_ids if command.walnut_ids else None,
        )

        # Create comparison entity (domain validation happens here - will return error if < 2 walnuts)
        comparison_entity_result = WalnutComparisonEntity.create(
            walnuts=walnut_entities,
            width_weight=command.width_weight,
            height_weight=command.height_weight,
            thickness_weight=command.thickness_weight,
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
            saved_comparisons = self.walnut_comparison_writer.bulk_save_or_update(comparison_daos)

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

