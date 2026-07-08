"""Cache file paths and ast.parse calls on them."""

import ast
from functools import cache
from pathlib import Path

MODULE_DIR = Path("src", "chezmoi_mousse")


@cache
def get_file_paths() -> tuple[Path, ...]:
    # This works because pytest sets the cwd to the project root.
    return tuple(MODULE_DIR.rglob("*.py"))


@cache
def ast_parse(py_file: Path) -> ast.AST:
    return ast.parse(py_file.read_text(encoding="utf-8"))
