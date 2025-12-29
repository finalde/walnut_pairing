# batch/application.py
from application_layer.commands.command_dispatcher import ICommandDispatcher
from application_layer.queries.walnut__query import WalnutQuery
from application_layer.commands.command_objects.walnut_command import (
    CreateFakeWalnutCommand,
)


class IApplication:
    pass


class Application:
    def __init__(
        self,
        command_dispatcher: ICommandDispatcher,
        walnut_query: WalnutQuery,
    ) -> None:
        self.command_dispatcher: ICommandDispatcher = command_dispatcher
        self.walnut_query: WalnutQuery = walnut_query

    def run(self) -> None:
        command = CreateFakeWalnutCommand(walnut_id="WALNUT-TEST-001")
        self.command_dispatcher.dispatch(command)
        
        fake_walnut = self.walnut_query.get_by_id("WALNUT-TEST-001")
        if fake_walnut:
            print(f"Query result: Found walnut {fake_walnut.walnut_id} with {len(fake_walnut.images)} images")
            for img in fake_walnut.images:
                print(
                    f"  - {img.side}: image_id={img.image_id}, "
                    f"embedding_id={img.embedding_id}"
                )

        print("\n--- Testing Query: Load Walnut from Filesystem ---")
        try:
            loaded_walnut = self.walnut_query.load_from_filesystem("0001")
            if loaded_walnut:
                print(f"Query result: Found walnut {loaded_walnut.walnut_id} with {len(loaded_walnut.images)} images")
                for img in loaded_walnut.images:
                    print(
                        f"  - {img.side}: image_path={img.image_path}, "
                        f"width={img.width}, height={img.height}"
                    )
            else:
                print("No walnut found in filesystem")
        except Exception as e:
            print(f"Error loading walnut from filesystem: {e}")
            import traceback
            traceback.print_exc()

        print("\n--- Testing CQRS: Get All Walnuts Query ---")
        all_walnuts = self.walnut_query.get_all()
        print(f"Query result: Found {len(all_walnuts)} walnuts in database")
