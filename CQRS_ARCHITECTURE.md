# CQRS Architecture

This codebase implements Command Query Responsibility Segregation (CQRS) pattern along with Domain-Driven Design (DDD).

## Structure

```
libs/application_layer/
├── queries/                    # Query side (read operations - synchronous)
│   └── walnut__query.py       # Walnut-specific queries (uses __ naming)
├── dtos/                       # Data Transfer Objects (returned by queries)
│   ├── walnut__dto.py          # Walnut DTOs
│   └── walnut__create_dto.py   # Create DTOs
│
├── commands/                   # Command side (write operations)
│   ├── command_dispatcher.py   # Command routing and execution
│   ├── command_objects/        # Command DTOs
│   │   ├── base__command.py    # Base command interface
│   │   └── walnut__command.py  # CreateWalnutFromImagesCommand, CompareWalnutsCommand
│   └── command_handlers/       # Command handlers
│       ├── base__command_handler.py  # Base handler interface
│       ├── walnut__command_handler.py
│       └── walnut_comparison__command_handler.py
```

## How It Works

### 1. Queries (Read Operations)

Queries are synchronous read operations that can return either DTOs (for API) or Domain Entities (for internal use):

```python
# Query to get DTOs for API (returns List[WalnutDTO])
all_walnuts_dto = self.walnut_query.get_all()

# Query to get entities for internal domain operations (returns List[WalnutEntity])
all_walnuts_entities = self.walnut_query.get_all_entities()
```

**Query Flow (DTOs for API):**
1. Query object uses infrastructure layer readers directly
2. Readers return DAOs from database/file
3. Mapper converts DAOs to DTOs
4. Returns DTOs to application layer (no domain knowledge exposed)

**Query Flow (Entities for Internal Use):**
1. Query object uses infrastructure layer readers directly
2. Readers return DAOs from database/file
3. Mapper converts DAOs to Domain Entities (using domain factories)
4. Returns Entities to command handlers for domain operations
5. Only entities with valid dimensions are returned (filtered during conversion)

### 2. Commands (Write Operations)

Commands trigger business operations and modify state:

```python
# Create and execute a command
compare_command = CompareWalnutsCommand(
    comparison_mode=ComparisonModeEnum.BOTH,
    width_weight=0.40,
    # ... all required parameters from config
    walnut_ids=None  # None means compare all walnuts
)
self.command_dispatcher.dispatch(compare_command)
```

**Command Flow:**
1. **Command Creation**: Application creates command object with all required parameters (typically from config)
2. **Dispatch**: Application calls `command_dispatcher.dispatch(command)`
3. **Handler Resolution**: Dispatcher finds registered handler for command type (registered via `CommandDispatcher.create_with_handlers()`)
4. **Handler Execution** (synchronous):
   - Gets domain entities via queries (`get_entities_by_ids()` or `get_all_entities()`)
   - Creates domain entity for orchestration (e.g., `WalnutComparisonEntity.create()`)
   - Executes domain logic (e.g., `comparison_entity.compare_all()`)
   - Maps domain results (value objects) to DAOs via mappers
   - Bulk saves to database via infrastructure writers
5. **Error Handling**: Domain errors are logged, exceptions are raised for infrastructure errors

## Command Handler Registration

Command handlers are registered in the DI container setup:

```python
# In CommandDispatcher.create_with_handlers()
dispatcher = CommandDispatcher()
create_handler = dependency_provider.resolve(CreateWalnutFromImagesHandler)
dispatcher.register_handler(CreateWalnutFromImagesCommand, create_handler)
```

Handlers are resolved from the DI container, ensuring all dependencies are injected.

## Benefits

1. **Separation of Concerns**: Read and write operations are clearly separated
2. **Scalability**: Read and write models can be optimized independently
3. **Domain Logic Isolation**: Business logic lives in domain entities, not command handlers
4. **Testability**: Commands and queries can be tested independently
5. **Extensibility**: Easy to add new commands/queries without modifying existing code
6. **Type Safety**: Command handlers are typed with `ICommandHandler[CommandType]`
7. **Bulk Operations**: Command handlers can perform bulk operations efficiently (e.g., `bulk_save_or_update()`)

## Key Patterns

### Command Handler Pattern
- Handlers orchestrate, domain entities execute business logic
- Handlers use queries to get entities, not DTOs
- Domain entities return value objects, handlers map to DAOs
- Use bulk operations when possible

### Query Pattern
- Separate methods for DTOs (API) and Entities (internal)
- Queries filter invalid entities during conversion
- Mappers handle DAO → Entity conversion using domain factories

