import ast

import pytest
from _test_utils import get_module_paths

MODULE_PATHS = get_module_paths()
# Exclude these enums as they are used in dynamically by FilteredDirTree
EXCLUDE_ENUMS = ["PwMgrInfo", "UnwantedDirs", "UnwantedFileExtensions"]


def _get_module_for_enum_class(enum_class_def: ast.ClassDef) -> str:
    # Find which module file contains the given enum class definition.
    for file_path in MODULE_PATHS:
        tree = ast.parse(file_path.read_text())
        for node in tree.body:
            if (
                isinstance(node, ast.ClassDef)
                and node.name == enum_class_def.name
            ):
                return str(file_path)
    return "unknown"


def _enum_ast_class_defs() -> list[ast.ClassDef]:
    enum_class_defs: list[ast.ClassDef] = []

    for file_path in MODULE_PATHS:
        tree = ast.parse(file_path.read_text())
        # Only check top-level nodes (direct children of the module)
        for node in tree.body:
            # Check if this is a class that inherits from Enum or StrEnum
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if (
                        isinstance(base, ast.Name)
                        and base.id in ("Enum", "StrEnum")
                        and node.name not in EXCLUDE_ENUMS
                    ):
                        enum_class_defs.append(node)
    return enum_class_defs


def _non_enum_ast_class_defs() -> list[ast.ClassDef]:
    class_defs: list[ast.ClassDef] = []

    for file_path in MODULE_PATHS:
        tree = ast.parse(file_path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if this class is NOT an enum
                is_enum = False
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id in (
                        "Enum",
                        "StrEnum",
                    ):
                        is_enum = True
                        break

                # If it's not an enum, add it to the list
                if not is_enum:
                    class_defs.append(node)

    return class_defs


def _class_has_getattr_for_enum(enum_class_name: str) -> bool:
    for class_def in _non_enum_ast_class_defs():
        for node in ast.walk(class_def):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if (
                    node.func.id == "getattr"
                    and len(node.args) >= 2
                    and isinstance(node.args[0], ast.Name)
                    and node.args[0].id == enum_class_name
                ):
                    return True
    return False


def _class_has_field_name(class_def: ast.ClassDef, member_name: str) -> bool:
    for node in ast.walk(class_def):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == member_name
        ):
            return True
    return False


@pytest.mark.parametrize(
    "enum_class_def", _enum_ast_class_defs(), ids=lambda x: x.name
)
def test_members_in_use(enum_class_def: ast.ClassDef):
    top_level_enum_members: list[ast.Assign] = [
        node for node in enum_class_def.body if isinstance(node, ast.Assign)
    ]
    not_in_use: list[str] = []

    for member in top_level_enum_members:
        # Get the member name from the assignment target
        if isinstance(member.targets[0], ast.Name):
            member_name = member.targets[0].id
        else:
            # This should not happen in enums, loop for type hinting
            continue

        found_usage: bool = False

        # Search for usage across non-enum class definitions
        for class_def in _non_enum_ast_class_defs():
            if found_usage:
                break

            for node in ast.walk(class_def):
                if isinstance(node, ast.Attribute):
                    # Check for direct member access (ClassName.member_name)
                    if isinstance(node.value, ast.Name):
                        if (
                            node.value.id == enum_class_def.name
                            and node.attr == member_name
                        ):
                            found_usage = True
                            break
                    elif isinstance(node.value, ast.Attribute):
                        # Check for access like module.ClassName.member_name
                        if (
                            isinstance(node.value.value, ast.Name)
                            and node.value.attr == enum_class_def.name
                            and node.attr == member_name
                        ):
                            found_usage = True
                            break
                elif isinstance(node, ast.AnnAssign):
                    # Check for annotated assignments with field names matching enum members
                    if (
                        isinstance(node.target, ast.Name)
                        and node.target.id == member_name
                    ):
                        # Check if ANY class in the codebase uses getattr with this enum class
                        if _class_has_getattr_for_enum(enum_class_def.name):
                            found_usage = True
                            break
                elif isinstance(node, ast.Call):
                    # Check for getattr(EnumClass, member_name) calls
                    if (
                        isinstance(node.func, ast.Name)
                        and node.func.id == "getattr"
                        and len(node.args) >= 2
                    ):
                        # Check if first arg is the enum class
                        if (
                            isinstance(node.args[0], ast.Name)
                            and node.args[0].id == enum_class_def.name
                        ):
                            # Check if second arg could be our member
                            if (
                                isinstance(node.args[1], ast.Constant)
                                and node.args[1].value == member_name
                            ):
                                found_usage = True
                                break
                            elif isinstance(
                                node.args[1], ast.Name
                            ) and _class_has_field_name(
                                class_def, member_name
                            ):
                                found_usage = True
                                break

        # If not found in non-enum classes, search in enum classes
        if not found_usage:
            for other_enum_def in _enum_ast_class_defs():
                if found_usage:
                    break

                # Skip the same enum class
                if other_enum_def.name == enum_class_def.name:
                    continue

                for node in ast.walk(other_enum_def):
                    if isinstance(node, ast.Attribute):
                        # Check for direct member access (ClassName.member_name)
                        if isinstance(node.value, ast.Name):
                            if (
                                node.value.id == enum_class_def.name
                                and node.attr == member_name
                            ):
                                found_usage = True
                                break
                        elif isinstance(node.value, ast.Attribute):
                            # Check for access like module.ClassName.member_name
                            if (
                                isinstance(node.value.value, ast.Name)
                                and node.value.attr == enum_class_def.name
                                and node.attr == member_name
                            ):
                                found_usage = True
                                break

        if found_usage is False:
            not_in_use_item = f"{enum_class_def.name}.{member_name} (in {_get_module_for_enum_class(enum_class_def)})"
            not_in_use.append(not_in_use_item)

    # Report all unused members at once
    if not_in_use:
        pytest.fail(f"Unused enum members:\n{'\n'.join(not_in_use)}")
