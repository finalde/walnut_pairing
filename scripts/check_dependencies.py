#!/usr/bin/env python3
"""Script to check dependency constraints at compile time."""
import ast
import sys
from pathlib import Path
from typing import List, Tuple

# Define allowed dependencies for each layer
DEPENDENCY_RULES = {
    "domain_layer": {
        "allowed": ["common"],
        "forbidden": ["application_layer", "infrastructure_layer", "app__webapi", "app__batch"],
    },
    "application_layer": {
        "allowed": ["domain_layer", "common", "infrastructure_layer"],  # infrastructure via interfaces only
        "forbidden": ["app__webapi", "app__batch"],
    },
    "infrastructure_layer": {
        "allowed": ["common"],
        "forbidden": ["domain_layer", "application_layer", "app__webapi", "app__batch"],
    },
    "common": {
        "allowed": ["common"],  # Can only depend on itself
        "forbidden": ["domain_layer", "application_layer", "infrastructure_layer", "app__webapi", "app__batch"],
    },
    "app__webapi": {
        "allowed": ["application_layer", "common"],
        "forbidden": ["domain_layer", "infrastructure_layer", "app__batch"],
    },
    "app__batch": {
        "allowed": ["application_layer", "common"],
        "forbidden": ["domain_layer", "infrastructure_layer", "app__webapi"],
    },
}


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to extract imports."""

    def __init__(self) -> None:
        self.imports: List[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.imports.append(node.module)
        self.generic_visit(node)


def get_layer_from_path(file_path: Path) -> str:
    """Determine which layer a file belongs to."""
    parts = file_path.parts
    if "domain_layer" in parts:
        return "domain_layer"
    elif "application_layer" in parts:
        return "application_layer"
    elif "infrastructure_layer" in parts:
        return "infrastructure_layer"
    elif "common" in parts:
        return "common"
    elif "app__webapi" in parts:
        return "app__webapi"
    elif "app__batch" in parts:
        return "app__batch"
    return "unknown"


def check_file(file_path: Path) -> List[Tuple[str, str]]:
    """Check a single file for dependency violations."""
    violations: List[Tuple[str, str]] = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        visitor = ImportVisitor()
        visitor.visit(tree)
        
        layer = get_layer_from_path(file_path)
        if layer == "unknown":
            return violations
        
        rules = DEPENDENCY_RULES.get(layer, {})
        allowed = rules.get("allowed", [])
        forbidden = rules.get("forbidden", [])
        
        for import_name in visitor.imports:
            # Check if import violates rules
            for forbidden_prefix in forbidden:
                if import_name.startswith(forbidden_prefix):
                    violations.append((str(file_path), f"Import '{import_name}' violates dependency constraint for {layer} layer"))
            
            # Special check: infrastructure_layer should not import domain_layer directly
            if layer == "infrastructure_layer" and import_name.startswith("domain_layer"):
                violations.append((str(file_path), f"Infrastructure layer cannot import from domain_layer: '{import_name}'"))
            
            # Special check: app__webapi/app__batch should not import domain_layer or infrastructure_layer directly
            if layer in ["app__webapi", "app__batch"]:
                if import_name.startswith("domain_layer"):
                    violations.append((str(file_path), f"{layer} cannot import from domain_layer directly, use DTOs from application_layer: '{import_name}'"))
                if import_name.startswith("infrastructure_layer"):
                    violations.append((str(file_path), f"{layer} cannot import from infrastructure_layer directly, use application_layer interfaces: '{import_name}'"))
    
    except Exception as e:
        violations.append((str(file_path), f"Error parsing file: {e}"))
    
    return violations


def main() -> int:
    """Main entry point."""
    project_root = Path(__file__).resolve().parent.parent
    violations: List[Tuple[str, str]] = []
    
    # Check all Python files in libs/ and app__*/
    for pattern in ["libs/**/*.py", "app__webapi/**/*.py", "app__batch/**/*.py"]:
        for file_path in project_root.glob(pattern):
            if file_path.name == "__init__.py" or "__pycache__" in str(file_path):
                continue
            file_violations = check_file(file_path)
            violations.extend(file_violations)
    
    if violations:
        print("❌ Dependency constraint violations found:\n")
        for file_path, message in violations:
            print(f"  {file_path}: {message}")
        return 1
    
    print("✅ All dependency constraints satisfied")
    return 0


if __name__ == "__main__":
    sys.exit(main())

