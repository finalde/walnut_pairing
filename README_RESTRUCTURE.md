# Codebase Restructure

The codebase has been restructured to support two executable applications:

## New Structure

```
walnut_pairing/
├── libs/              # Shared library code
│   └── src/           # All shared business logic, domain, infrastructure
├── app__batch/        # Batch job application
│   ├── main.py        # Batch entry point
│   ├── application.py # Batch-specific application logic
│   └── config.yml     # Batch configuration
└── app__webapi/       # FastAPI web application
    ├── main.py        # FastAPI entry point
    ├── dependencies.py # DI setup for web API
    ├── routes/        # API routes
    │   └── walnuts.py
    └── config.yml     # Web API configuration
```

## Running Applications

### Batch Job
```bash
cd batch
python main.py
```

### Web API
```bash
cd webapi
python main.py
# Or with uvicorn:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Configuration

Each application has its own `config.yml` file:
- `app__batch/config.yml` - Batch job configuration
- `app__webapi/config.yml` - Web API configuration

Both can share the same database and image root settings, or be configured independently.

## Dependencies

All shared dependencies are in `libs/src/`:
- `common/` - Interfaces, constants, enums, DI registry/container
- `application_layer/` - Application services and mappers
- `domain_layer/` - Domain entities, value objects, services
- `infrastructure_layer/` - DB readers/writers, file readers, DAOs, session factory
- `app_config.py` - Configuration management

## Import Paths

All code in `libs/src/` uses `src.*` imports (e.g., `from src.common.interfaces import ...`).

Both `app__batch/` and `app__webapi/` add `libs/` to `sys.path` to access shared code.

