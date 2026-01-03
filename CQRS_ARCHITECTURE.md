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
│   ├── command_objects/        # Command DTOs
│   │   ├── base_command.py
│   │   └── walnut_command.py
│   ├── command_handlers/      # Command handlers
│   │   ├── base_handler.py
│   │   ├── walnut_command_handler.py
│   │   └── walnut_event_handler.py
```

## How It Works

### 1. Queries (Read Operations)

Queries are synchronous read operations that return DTOs (not DAOs):

```python
# Query to get all walnuts (returns List[WalnutDTO])
all_walnuts = self.walnutr_query.get_all_walnuts()
```

**Query Flow:**
1. Query object uses infrastructure layer readers directly
2. Readers return DAOs from database/file
3. Use Mapper in Query converts DAOs to Domain Entity or ValueObject for domain level processing
4. Map to DTOs if need to expose to outside (no domain knowledge exposed)

### 2. Commands (Write Operations)

Commands trigger business operations and fire events:

```python
# Execute a command
 self.command_dispatcher.dispatch(compare_command)

```

**Command Flow:**
1. Command is created (e.g., `CompareWalnutsCommand`)
2. Based on the registration, the system find the best command handler to handle it
3. Handler executes the business logic

## Benefits

1. **Separation of Concerns**: Read and write operations are clearly separated
2. **Scalability**: Read and write models can be optimized independently
3. **Event-Driven**: Commands fire events, enabling event-driven architecture
4. **Flexibility**: Event handling can be sync or async
5. **Testability**: Commands and queries can be tested independently
6. **Extensibility**: Easy to add new commands/queries without modifying existing code

