import ast
from enum import StrEnum
from pathlib import Path

import chezmoi_mousse.id_typing._str_enums


def get_module_paths(
    exclude_paths: list[Path] = [], exclude_id_typing: bool = False
) -> list[Path]:
    src_dir = Path("./src/chezmoi_mousse")
    # the glob method returns an iterator of Path objects
    py_files = [f for f in src_dir.glob("**/*.py")]
    if exclude_id_typing:
        # remove all py files in the id_typing directory
        py_files = [f for f in py_files if "id_typing" not in f.parts]
    # exclude any additional specified paths
    py_files = [f for f in py_files if f not in exclude_paths]
    # exclude __init__.py and __main__.py files
    py_files = [
        f for f in py_files if f.name not in ("__init__.py", "__main__.py")
    ]
    return py_files


def get_module_ast_tree(module_path: Path) -> ast.AST:
    return ast.parse(module_path.read_text())


def get_str_enum_classes() -> list[type[StrEnum]]:
    return [
        cls
        for cls in chezmoi_mousse.id_typing._str_enums.__dict__.values()
        if isinstance(cls, type) and issubclass(cls, StrEnum)
    ]


def get_modules_importing_class(class_name: str) -> list[Path]:
    modules: list[Path] = []
    for module_path in get_module_paths(
        exclude_paths=[Path("id_typing", "enums.py")]
    ):
        tree = ast.parse(module_path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if class_name in (alias.name for alias in node.names):
                    modules.append(module_path)
    return modules
