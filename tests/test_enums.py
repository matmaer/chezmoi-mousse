import ast
from collections.abc import Iterator
from pathlib import Path

import pytest
from _test_utils import get_module_ast_class_defs, get_module_paths

BASE_DIR = "src/chezmoi_mousse"
ID_CLASSES_PATH = Path("src/chezmoi_mousse/_id_classes.py")


def _get_enum_ast_class_defs() -> list[ast.ClassDef]:
    file_paths: Iterator[Path] = Path(BASE_DIR).rglob("*.py")
    enum_class_defs: list[ast.ClassDef] = []
    excluded_dirs = {"gui"}  # Add more directories to exclude if needed

    for file_path in file_paths:
        # Skip files in excluded subdirectories
        if any(part in excluded_dirs for part in file_path.parts):
            continue

        tree = ast.parse(file_path.read_text())
        for node in ast.walk(tree):
            # Check if this is a class that inherits from Enum or StrEnum
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id in (
                        "Enum",
                        "StrEnum",
                    ):
                        enum_class_defs.append(node)
                        break
    return enum_class_defs


def _get_enum_assign_members(class_def: ast.ClassDef) -> Iterator[ast.Assign]:
    for node in class_def.body:
        if isinstance(node, ast.Assign):
            yield node


@pytest.mark.parametrize(
    "enum_class_def", _get_enum_ast_class_defs(), ids=lambda x: x.name
)
def test_members_in_use(enum_class_def: ast.ClassDef):
    enum_members: Iterator[ast.Assign] = _get_enum_assign_members(
        enum_class_def
    )
    not_in_use: list[str] = []

    for member in enum_members:
        # Get the member name from the assignment target
        if isinstance(member.targets[0], ast.Name):
            member_name = member.targets[0].id
        else:
            continue  # Skip if we can't get the member name

        not_in_use_item = f"{enum_class_def.name}.{member_name}"
        found_usage: bool = False

        # First check if the member is used in other enum classes
        for enum_class in _get_enum_ast_class_defs():
            if enum_class.name == enum_class_def.name:
                continue  # Skip the same enum class

            for node in ast.walk(enum_class):
                if isinstance(node, ast.Attribute):
                    # Check for direct member access (ClassName.member_name)
                    if (
                        isinstance(node.value, ast.Name)
                        and node.value.id == enum_class_def.name
                        and node.attr == member_name
                    ):
                        found_usage = True
                        break
                    # Check for .name/.value access (ClassName.member_name.name/value)
                    elif (
                        isinstance(node.value, ast.Attribute)
                        and isinstance(node.value.value, ast.Name)
                        and node.value.value.id == enum_class_def.name
                        and node.value.attr == member_name
                        and node.attr in ("name", "value")
                    ):
                        found_usage = True
                        break
            if found_usage:
                break

        # If not found in enum classes, check in regular module classes
        if not found_usage:
            # check if the member is in use looping over all module paths
            for module_path in get_module_paths() + [ID_CLASSES_PATH]:
                found_usage_in_module: bool = False
                module_class_defs = get_module_ast_class_defs(module_path)

                # check if the member is in use looping over all module class defs
                for class_def in module_class_defs:
                    class_tree = ast.walk(class_def)
                    # Look for attribute access to this enum member
                    for node in class_tree:
                        if isinstance(node, ast.Attribute):
                            # Check for direct member access (ClassName.member_name)
                            if (
                                isinstance(node.value, ast.Name)
                                and node.value.id == enum_class_def.name
                                and node.attr == member_name
                            ):
                                found_usage_in_module = True
                                break
                            # Check for .name/.value access (ClassName.member_name.name/value)
                            elif (
                                isinstance(node.value, ast.Attribute)
                                and isinstance(node.value.value, ast.Name)
                                and node.value.value.id == enum_class_def.name
                                and node.value.attr == member_name
                                and node.attr in ("name", "value")
                            ):
                                found_usage_in_module = True
                                break
                    if found_usage_in_module:
                        break

                if found_usage_in_module:
                    found_usage = True
                    break  # Move to next member as soon as usage is found

        if found_usage is False:
            not_in_use.append(not_in_use_item)

    # Report all unused members at once
    if not_in_use:
        pytest.fail(f"Unused enum members:\n{'\n'.join(not_in_use)}")
