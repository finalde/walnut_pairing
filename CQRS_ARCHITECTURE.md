# CQRS Architecture

This codebase implements Command Query Responsibility Segregation (CQRS) pattern along with Domain-Driven Design (DDD).

## Structure

```
libs/src/application_layer/
├── queries/                    # Query side (read operations - synchronous)
│   └── walnut__query.py       # Walnut-specific queries (uses __ naming)
├── dtos/                       # Data Transfer Objects (returned by queries)
│   └── walnut__dto.py          # Walnut DTOs
│
├── commands/                   # Command side (write operations)
│   ├── command_bus.py         # Command bus for dispatching commands
│   ├── command_objects/        # Command DTOs
│   │   ├── base_command.py
│   │   └── walnut_command.py
│   ├── command_handlers/      # Command handlers
│   │   ├── base_handler.py
│   │   ├── walnut_command_handler.py
│   │   └── walnut_event_handler.py
│   └── command_events/         # Events fired by commands
│       ├── base_event.py
│       ├── event_bus.py       # Event bus (sync/async/Kafka)
│       └── walnut_event.py
│
└── cqrs_facade.py             # Facade for easy access to queries/commands
```

## How It Works

### 1. Queries (Read Operations)

Queries are synchronous read operations that return DTOs (not DAOs):

```python
# In batch/webapi code:
cqrs = container.cqrs_facade()

# Query to get a walnut (returns WalnutDTO)
walnut = cqrs.get_walnut_by_id("0001")

# Query to get all walnuts (returns List[WalnutDTO])
all_walnuts = cqrs.get_all_walnuts()
```

**Query Flow:**
1. Query object uses infrastructure layer readers directly
2. Readers return DAOs from database/file
3. Query converts DAOs to DTOs
4. DTOs are returned (no domain knowledge exposed)

### 2. Commands (Write Operations)

Commands trigger business operations and fire events:

```python
# Execute a command
cqrs.create_fake_walnut("WALNUT-001")
cqrs.load_walnut_from_filesystem("0001")
```

**Command Flow:**
1. Command is created (e.g., `CreateFakeWalnutCommand`)
2. Command is sent to `CommandBus`
3. `CommandBus` finds the appropriate handler
4. Handler executes the business logic
5. Handler publishes events to `EventBus`
6. Event handlers react to events

### 3. Events

Events are fired by command handlers and can be handled synchronously or asynchronously:

**Event Bus Types:**
- `SyncEventBus`: Events are handled immediately (default)
- `AsyncEventBus`: Events are queued and processed in background thread
- `KafkaEventBus`: Events are published to Kafka (placeholder, not implemented yet)

**Event Flow:**
1. Command handler publishes event to `EventBus`
2. `EventBus` notifies all subscribed handlers
3. Event handlers execute (sync or async based on bus type)

## Usage Examples

### Batch Application

```python
from src.common.di_container import Container
from src.application_layer.cqrs_facade import CQRSFacade

container = Container()
cqrs = container.cqrs_facade()

# Query
walnuts = cqrs.get_all_walnuts()

# Command
cqrs.create_fake_walnut("WALNUT-001")
```

### Web API

```python
from fastapi import Depends
from src.application_layer.cqrs_facade import CQRSFacade

@router.get("/walnuts")
async def get_walnuts(cqrs: CQRSFacade = Depends(get_cqrs_facade)):
    return cqrs.get_all_walnuts()

@router.post("/walnuts/{walnut_id}/load")
async def load_walnut(walnut_id: str, cqrs: CQRSFacade = Depends(get_cqrs_facade)):
    cqrs.load_walnut_from_filesystem(walnut_id)
    return cqrs.get_walnut_by_id(walnut_id)
```

## Adding New Commands/Queries

### Adding a New Query

1. Add method to query class in `queries/walnut__query.py`:
```python
def get_by_description(self, description: str) -> List[WalnutDTO]:
    """Get walnuts by description."""
    walnut_daos = self.walnut_reader.get_by_description(description)
    return [self._dao_to_dto(dao) for dao in walnut_daos]
```

2. Add corresponding DTO if needed in `dtos/walnut__dto.py`

3. Add to `CQRSFacade`:
```python
def get_walnuts_by_description(self, description: str) -> List[WalnutDTO]:
    """Get walnuts by description."""
    return self.walnut_query.get_by_description(description)
```

**Note:** Queries are synchronous and use infrastructure readers directly. They return DTOs, not DAOs.

### Adding a New Command

1. Create command object in `commands/command_objects/walnut_command.py`:
```python
@dataclass
class UpdateWalnutDescriptionCommand(ICommand):
    walnut_id: str
    new_description: str
```

2. Create event in `commands/command_events/walnut_event.py`:
```python
@dataclass
class WalnutDescriptionUpdatedEvent(IEvent):
    walnut_id: str
    old_description: str
    new_description: str
```

3. Create handler in `commands/command_handlers/walnut_command_handler.py`:
```python
class UpdateWalnutDescriptionHandler(ICommandHandler[UpdateWalnutDescriptionCommand]):
    def handle(self, command: UpdateWalnutDescriptionCommand) -> None:
        # Business logic
        # Publish event
        event = WalnutDescriptionUpdatedEvent(...)
        self.event_bus.publish(event)
```

4. Register handler in `di_container.py` `_create_command_bus_with_deps()`:
```python
update_handler = UpdateWalnutDescriptionHandler(...)
command_bus.register_handler(UpdateWalnutDescriptionCommand, update_handler)
```

5. Add to `CQRSFacade`:
```python
def update_walnut_description(self, walnut_id: str, new_description: str) -> None:
    command = UpdateWalnutDescriptionCommand(
        walnut_id=walnut_id,
        new_description=new_description,
    )
    self.command_bus.execute(command)
```

## Event Bus Configuration

Currently, the event bus defaults to `SyncEventBus`. To use async:

1. Modify `create_event_bus()` in `di_container.py`:
```python
def create_event_bus(app_config: IAppConfig) -> "IEventBus":
    # Check config for event bus type
    if app_config.get("event_bus_type") == "async":
        return AsyncEventBus()
    return SyncEventBus()
```

2. For Kafka (future):
```python
if app_config.get("event_bus_type") == "kafka":
    return KafkaEventBus(kafka_config=app_config.kafka_config)
```

## Benefits

1. **Separation of Concerns**: Read and write operations are clearly separated
2. **Scalability**: Read and write models can be optimized independently
3. **Event-Driven**: Commands fire events, enabling event-driven architecture
4. **Flexibility**: Event handling can be sync or async
5. **Testability**: Commands and queries can be tested independently
6. **Extensibility**: Easy to add new commands/queries without modifying existing code

