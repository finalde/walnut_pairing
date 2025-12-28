# Code Quality Standards

This project maintains high code quality standards through strict type checking and linting.

## Tools

- **mypy**: Static type checking with strict mode enabled
- **flake8**: Linting with multiple plugins for comprehensive checks
- **black**: Code formatting (enforced)
- **isort**: Import sorting (enforced)

## Running Checks

### Quick Check (All at once)
```bash
make check
# or
./scripts/check_code_quality.sh
```

### Individual Checks
```bash
# Type checking
make type-check
# or
mypy walnut_pair_backend/src

# Linting
make lint
# or
flake8 walnut_pair_backend/src

# Format checking
make format-check
```

### Auto-fix Issues
```bash
# Auto-fix formatting and import order
make fix
# or
./scripts/fix_code_quality.sh
```

## Type Checking Standards

- **Strict mode**: All functions must have type hints
- **No untyped calls**: Cannot call functions without type hints
- **Complete definitions**: All function parameters and return types must be typed
- **Type safety**: Use `Optional`, `Union`, and proper generic types

## Linting Standards

- **Max line length**: 88 characters (Black standard)
- **Complexity**: Maximum cyclomatic complexity of 10
- **Import order**: Google style (enforced by isort)
- **Docstrings**: Encouraged for public APIs

## Pre-commit Hooks (Recommended)

Install pre-commit hooks to automatically check code before commits:

```bash
pip install pre-commit
pre-commit install
```

## CI/CD Integration

The project includes a `Makefile` with a `ci` target that runs all checks:

```bash
make ci
```

This should be integrated into your CI/CD pipeline to ensure code quality on every commit.

## Common Issues and Fixes

### Type Errors
- Add type hints to all function parameters and return types
- Use `Optional[Type]` for nullable values
- Use proper generic types (e.g., `List[str]` instead of `list`)

### Import Order
- Run `isort walnut_pair_backend/src` to auto-fix
- Follow Google import style: stdlib, third-party, local

### Formatting
- Run `black walnut_pair_backend/src` to auto-fix
- Follow Black's formatting rules (line length 88)

### Linting Issues
- Fix complexity issues by breaking down complex functions
- Remove unused imports
- Follow PEP 8 style guidelines

