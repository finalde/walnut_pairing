#!/bin/bash
# Script to run all code quality checks: mypy, flake8, black, isort

set -e  # Exit on error

echo "🔍 Running code quality checks..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to project root
cd "$(dirname "$0")/.."

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}Warning: Virtual environment not activated. Some checks may fail.${NC}"
fi

# Run isort to check import order
echo "📦 Checking import order with isort..."
if isort --check-only --diff walnut_pair_backend/src; then
    echo -e "${GREEN}✓ Import order is correct${NC}"
else
    echo -e "${RED}✗ Import order issues found. Run: isort walnut_pair_backend/src${NC}"
    exit 1
fi
echo ""

# Run black to check formatting
echo "🎨 Checking code formatting with black..."
if black --check --diff walnut_pair_backend/src; then
    echo -e "${GREEN}✓ Code formatting is correct${NC}"
else
    echo -e "${RED}✗ Formatting issues found. Run: black walnut_pair_backend/src${NC}"
    exit 1
fi
echo ""

# Run flake8 for linting
echo "🔎 Running flake8 linting..."
if flake8 walnut_pair_backend/src; then
    echo -e "${GREEN}✓ Flake8 checks passed${NC}"
else
    echo -e "${RED}✗ Flake8 found issues${NC}"
    exit 1
fi
echo ""

# Run mypy for type checking
echo "🔬 Running mypy type checking..."
if mypy walnut_pair_backend/src; then
    echo -e "${GREEN}✓ Type checking passed${NC}"
else
    echo -e "${RED}✗ Type checking found issues${NC}"
    exit 1
fi
echo ""

echo -e "${GREEN}✅ All code quality checks passed!${NC}"

