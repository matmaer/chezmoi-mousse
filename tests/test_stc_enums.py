"""Test if all members from the StrEnum classes in _str_enums.py are in use"""

import ast
from enum import StrEnum
from pathlib import Path
from types import ModuleType

import pytest
from _test_utils import get_module_paths

import chezmoi_mousse._str_enums as str_enums


def _get_strenum_classes(from_module: ModuleType) -> list[type[StrEnum]]:
    classes: list[type[StrEnum]] = []
    # Get the module's source file path
    if from_module.__file__ is None:
        return classes
    module_file = Path(from_module.__file__)
    # Read and parse the source code
    content = module_file.read_text()
    tree = ast.parse(content, filename=str(module_file))
    # Find class definitions that inherit from StrEnum
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == "StrEnum":
                    # Get the class object from the module
                    enum_class = getattr(from_module, node.name, None)
                    if enum_class and issubclass(enum_class, StrEnum):
                        classes.append(enum_class)
                    break  # No need to check other bases for this class
    return classes


def _find_enum_usage_in_file(
    py_file: Path, enum_class_name: str, member_name: str
) -> tuple[bool, bool]:
    """Find if enum member is used and if .value is unnecessarily used.

    Returns:
        (found_usage, has_unnecessary_value_usage)
    """
    content = py_file.read_text()
    tree = ast.parse(content, filename=str(py_file))

    found_usage = False
    unnecessary_value_usage = False

    for node in ast.walk(tree):
        # Look for Attribute nodes like EnumClass.member
        if isinstance(node, ast.Attribute):
            # Check for EnumClass.member usage
            if (
                isinstance(node.value, ast.Name)
                and node.value.id == enum_class_name
                and node.attr == member_name
            ):
                found_usage = True

            # Check for unnecessary .value usage: EnumClass.member.value
            elif (
                isinstance(node.value, ast.Attribute)
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id == enum_class_name
                and node.value.attr == member_name
                and node.attr == "value"
            ):
                unnecessary_value_usage = True
                found_usage = True  # It's still usage, just bad usage

    return found_usage, unnecessary_value_usage


@pytest.mark.parametrize(
    "str_enum_class",
    _get_strenum_classes(str_enums),
    ids=lambda cls: cls.__name__,
)
def test_strenum_members_in_use(str_enum_class: type[StrEnum]):
    enum_class_name = str_enum_class.__name__
    modules = get_module_paths(
        exclude_file_names=["custom_theme.py", "_str_enums.py"]
    )

    members_with_unnecessary_value: list[str] = []
    error_messages: list[str] = []
    unused_members: list[str] = []

    for member in str_enum_class:
        member_name = member.name
        found = False

        for py_file in modules:
            usage_found, value_unnecessary = _find_enum_usage_in_file(
                py_file, enum_class_name, member_name
            )
            if usage_found:
                found = True
            if value_unnecessary:
                members_with_unnecessary_value.append(
                    f"{member_name} in {py_file.parts[-1]}"
                )

        if not found:
            unused_members.append(member_name)

    # Report failures
    if unused_members:
        error_messages.append(
            f"Unused members in {enum_class_name}: {', '.join(unused_members)}"
        )

    if members_with_unnecessary_value:
        error_messages.append(
            f"Members with unnecessary .value attribute in {enum_class_name}: {', '.join(members_with_unnecessary_value)}"
        )

    if error_messages:
        pytest.fail("\n" + "\n".join(error_messages))
