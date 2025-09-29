"""Test if all class members are in use."""

import ast
from dataclasses import dataclass
from pathlib import Path
from pprint import pprint

from _test_utils import modules_to_test

# def modules_to_test(exclude_file_names: list[str] = []) -> list[Path]:
#     src_dir = Path("./src/chezmoi_mousse")
#     return [
#         f for f in src_dir.glob("*.py") if f.name not in exclude_file_names
#     ]


# modules = modules_to_test()
# pprint(modules)


def get_module_classes_from_ast(file_path: Path) -> list[str] | None:
    """Get all class names defined in a Python file by parsing its AST."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    tree = ast.parse(content)
    classes: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)

    return classes if classes else None


# get_module_classes_from_ast(modules[1])


@dataclass
class ModuleClasses:
    module: Path
    classes: list[str] | None


module_classes: list[ModuleClasses] = [
    ModuleClasses(module=module, classes=classes)
    for module in modules_to_test()
    if (classes := get_module_classes_from_ast(module)) is not None
]

pprint(module_classes)
