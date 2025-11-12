import ast
from collections.abc import Iterator
from typing import NamedTuple

import pytest
from _test_utils import get_module_ast_class_defs, get_module_paths

type AstClassDefs = list[ast.ClassDef]

MODULE_PATHS = get_module_paths()


def _is_enum_class(class_def: ast.ClassDef) -> bool:
    for base in class_def.bases:
        # direct name: Enum, StrEnum
        if isinstance(base, ast.Name) and base.id in ("Enum", "StrEnum"):
            return True
        # attribute: enum.Enum, enum.StrEnum
        if isinstance(base, ast.Attribute) and getattr(base, "attr", None) in (
            "Enum",
            "StrEnum",
        ):
            return True
    return False


class ClassData(NamedTuple):
    # tuple to avoid a flat with possible duplicate nodes
    module_path: str  # the module path for error reporting
    class_name: str  # the ast.ClassDef.name
    nodes: Iterator[ast.AST]  # the ast nodes within the class


enum_classes: list[ClassData] = []
non_enum_classes: list[ClassData] = []

for file_path in MODULE_PATHS:
    class_defs: AstClassDefs = get_module_ast_class_defs(file_path)
    for class_def in class_defs:
        to_append = ClassData(
            module_path=str(file_path),
            class_name=class_def.name,
            nodes=ast.walk(class_def),
        )
        if _is_enum_class(class_def):
            enum_classes.append(to_append)
        else:
            non_enum_classes.append(to_append)

###########################################
# Test if all enum class names are unique #
###########################################


def test_unique_enum_class_names() -> None:
    names_to_modules: dict[str, set[str]] = {}

    for item in enum_classes:
        names_to_modules.setdefault(item.class_name, set())
        names_to_modules[item.class_name].add(item.module_path)

    pytest_fail_messages: list[str] = []
    failed_names: list[str] = []
    for class_name, modules in names_to_modules.items():
        if len(modules) > 1:
            failed_names.append(class_name)
            pytest_fail_messages.append(
                f"{class_name} found in modules:\n- {'\n- '.join(sorted(modules))}"
            )

    if pytest_fail_messages:
        # Put a concise header on the first line so pytest's short summary
        # shows which enum class names failed.
        header = (
            f"Duplicate enum class names found: {', '.join(sorted(failed_names))}\n"
            if failed_names
            else ""
        )
        pytest.fail(header + "\n".join(pytest_fail_messages))
