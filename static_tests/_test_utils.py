"""Utility functions for static tests, with caching to speed up repeated access to
module data across the different test_ modules."""

import ast
from functools import cache
from pathlib import Path

BASE_DIR = Path("src", "chezmoi_mousse")


@cache
def get_module_paths() -> list[Path]:
    return list(BASE_DIR.glob("**/*.py"))


@cache
def get_gui_module_paths() -> list[Path]:
    all_modules = get_module_paths()
    gui_paths = [p for p in all_modules if "gui" in p.parts]
    debug_paths = [p for p in all_modules if "debug" in p.parts]
    app_path = [p for p in all_modules if "_textual_app.py" in p.parts]

    return [Path.cwd() / p for p in (gui_paths + debug_paths + app_path)]


@cache
def get_module_ast_tree(module_path: Path) -> ast.AST:
    return ast.parse(module_path.read_text())


@cache
def get_module_ast_class_defs(module_path: Path) -> list[ast.ClassDef]:
    class_defs: list[ast.ClassDef] = []
    for node in ast.walk(get_module_ast_tree(module_path)):
        if isinstance(node, ast.ClassDef):
            class_defs.append(node)
    return class_defs


@cache
def get_modules_importing_class(class_name: str) -> set[Path]:
    modules: set[Path] = set()
    for module_path in get_module_paths():
        for node in ast.walk(get_module_ast_tree(module_path)):
            if isinstance(node, ast.ImportFrom) and class_name in (
                alias.name for alias in node.names
            ):
                modules.add(module_path)
                break
    return modules
