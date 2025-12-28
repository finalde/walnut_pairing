.PHONY: help type-check lint format fix check install test

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	pip install -r requirements.txt

type-check: ## Run mypy type checking
	mypy walnut_pair_backend/src

lint: ## Run flake8 linting
	flake8 walnut_pair_backend/src

format-check: ## Check code formatting (black and isort)
	black --check walnut_pair_backend/src
	isort --check-only walnut_pair_backend/src

format: ## Auto-format code (black and isort)
	black walnut_pair_backend/src
	isort walnut_pair_backend/src

fix: format ## Auto-fix code issues (formatting and import order)
	@echo "✓ Code formatting and import order fixed"

check: type-check lint format-check ## Run all code quality checks
	@echo "✅ All checks passed!"

test: ## Run tests (placeholder)
	@echo "Tests not yet implemented"

ci: check ## Run all checks for CI/CD
	@echo "✅ CI checks completed"

