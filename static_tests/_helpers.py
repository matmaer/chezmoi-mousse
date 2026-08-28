import ast
from functools import cache
from pathlib import Path

__all__ = ["ast_parse", "get_file_paths"]

SRC_DIR = Path("src")
STATIC_TESTS_DIR = Path("static_tests")
MODULE_DIR = Path("src", "chezmoi_mousse")


@cache
def ast_parse(py_file: Path) -> ast.Module:
    return ast.parse(py_file.read_text(encoding="utf-8"))


def get_file_paths() -> list[Path]:
    return [Path(file_path) for file_path in MODULE_DIR.rglob("*.py")]
