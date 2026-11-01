import ast
import importlib
from pathlib import Path

import pytest

LAYERS = ["domain", "ai", "adapters", "api", "jobs", "config"]
DOMAIN_DIR = Path(__file__).parents[2] / "src" / "lodestar" / "domain"
FORBIDDEN_IN_DOMAIN = {f"lodestar.{layer}" for layer in LAYERS if layer != "domain"} | {
    "fastapi",
    "sqlalchemy",
    "sqlmodel",
}


@pytest.mark.parametrize("layer", LAYERS)
def test_layer_is_importable(layer: str) -> None:
    importlib.import_module(f"lodestar.{layer}")


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_domain_imports_no_outer_layer_or_framework() -> None:
    for path in DOMAIN_DIR.rglob("*.py"):
        for name in _imported_modules(path):
            assert not any(
                name == forbidden or name.startswith(f"{forbidden}.")
                for forbidden in FORBIDDEN_IN_DOMAIN
            ), f"{path.name} imports {name}"
