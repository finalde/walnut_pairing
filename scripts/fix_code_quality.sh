#!/bin/bash
# Script to automatically fix code quality issues: black, isort

set -e  # Exit on error

echo "🔧 Fixing code quality issues..."
echo ""

# Change to project root
cd "$(dirname "$0")/.."

# Run isort to fix import order
echo "📦 Fixing import order with isort..."
isort walnut_pair_backend/src
echo "✓ Import order fixed"
echo ""

# Run black to fix formatting
echo "🎨 Fixing code formatting with black..."
black walnut_pair_backend/src
echo "✓ Code formatting fixed"
echo ""

echo "✅ Code quality fixes applied!"
echo ""
echo "Note: You still need to manually fix any mypy type errors and flake8 issues."

