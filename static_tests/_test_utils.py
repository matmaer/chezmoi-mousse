"""Utility functions for static tests, with caching to speed up repeated access to
module data across the different test_ modules."""

import ast
from functools import cache
from pathlib import Path
from typing import NamedTuple

BASE_DIR = Path("src", "chezmoi_mousse")


class ModuleData(NamedTuple):
    module_path: str  # the module path for error reporting
    module_nodes: list[ast.AST]  # all ast nodes in the module (materialized)


@cache
def get_module_paths() -> list[Path]:
    py_files = list(BASE_DIR.glob("**/*.py"))
    py_files = [f for f in py_files if f.name not in ("__init__.py", "__main__.py")]
    return py_files


@cache
def get_gui_module_paths() -> list[Path]:
    return [Path.cwd() / p for p in get_module_paths() if "gui" in p.parts]


@cache
def get_module_ast_tree(module_path: Path) -> ast.AST:
    return ast.parse(module_path.read_text())


@cache
def get_exported_names(module_path: Path) -> set[str]:

    tree = get_module_ast_tree(module_path)

    for node in tree.body if isinstance(tree, ast.Module) else []:
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets)
            and isinstance(node.value, (ast.List, ast.Tuple))
        ):
            return {
                e.value
                for e in node.value.elts
                if isinstance(e, ast.Constant) and isinstance(e.value, str)
            }
    return set()


@cache
def get_module_ast_class_defs(module_path: Path) -> list[ast.ClassDef]:
    class_defs: list[ast.ClassDef] = []
    for node in ast.walk(get_module_ast_tree(module_path)):
        if isinstance(node, ast.ClassDef):
            class_defs.append(node)
    return class_defs


@cache
def get_all_module_data() -> list[ModuleData]:
    result: list[ModuleData] = []
    for file_path in get_module_paths():
        result.append(
            ModuleData(
                module_path=str(file_path),
                module_nodes=list(ast.walk(get_module_ast_tree(file_path))),
            )
        )
    return result


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
