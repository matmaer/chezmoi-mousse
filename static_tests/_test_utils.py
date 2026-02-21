import ast
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

BASE_DIR = Path("src", "chezmoi_mousse")


class ModuleData(NamedTuple):
    module_path: str  # the module path for error reporting
    module_nodes: list[ast.AST]  # all ast nodes in the module (materialized)


@lru_cache(maxsize=None)
def get_module_paths() -> list[Path]:
    py_files = [f for f in BASE_DIR.glob("**/*.py")]
    py_files = [f for f in py_files if f.name not in ("__init__.py", "__main__.py")]
    return py_files


@lru_cache(maxsize=None)
def get_module_ast_tree(module_path: Path) -> ast.AST:
    return ast.parse(module_path.read_text())


def get_module_ast_class_defs(module_path: Path) -> list[ast.ClassDef]:
    class_defs: list[ast.ClassDef] = []
    for node in ast.walk(get_module_ast_tree(module_path)):
        if isinstance(node, ast.ClassDef):
            class_defs.append(node)
    return class_defs


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


@lru_cache(maxsize=None)
def get_modules_importing_class(class_name: str) -> list[Path]:
    modules: list[Path] = []
    for module_path in get_module_paths():
        for node in ast.walk(get_module_ast_tree(module_path)):
            if isinstance(node, ast.ImportFrom):
                if class_name in (alias.name for alias in node.names):
                    modules.append(module_path)
                    break
    return modules
