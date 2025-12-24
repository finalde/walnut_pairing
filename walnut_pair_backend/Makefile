# Makefile for walnut_pairing_backend

PYTHON = python
SRC = src

all: validate run

# Type check
mypy:
	mypy $(SRC)

# Lint check
flake8:
	flake8 $(SRC)

# Run both mypy and flake8
validate: mypy flake8
	@echo "All checks passed ✅"

# Run backend main
run:
	$(PYTHON) -m $(SRC).main

# Clean __pycache__
clean:
	find $(SRC) -name "__pycache__" -type d -exec rm -r {} +
