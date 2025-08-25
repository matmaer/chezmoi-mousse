"""Test if all methods from the IdMixin are in use by modules in the src dir."""

import ast
import inspect
from enum import Enum, StrEnum
from pathlib import Path

import pytest
from _test_utils import modules_to_test

import chezmoi_mousse.id_typing as id_typing


@pytest.mark.parametrize(
    "py_file", modules_to_test(), ids=lambda py_file: py_file.name
)
def test_no_hardcoded_ids(py_file: Path):
    content = py_file.read_text()
    tree = ast.parse(content, filename=str(py_file))

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for keyword in node.keywords:
                if (
                    keyword.arg == "id"
                    and isinstance(keyword.value, ast.Constant)
                    and isinstance(keyword.value.value, str)
                ):
                    pytest.fail(
                        f"\nHardcoded id: line {keyword.lineno}: {keyword.value.value}"
                    )


def _get_str_enum_members() -> list[StrEnum]:
    members: list[StrEnum] = []
    for _, enum_class in inspect.getmembers(id_typing, inspect.isclass):
        if (
            issubclass(enum_class, StrEnum)
            and enum_class is not StrEnum  # exclude the StrEnum class itself
            # exclude TcssStr since it's tested in test_tcss.py
            and enum_class.__name__ != "TcssStr"
            # exclude strings used for filtering DirectoryTree
            # exclude PwMgrInfo members since they are dynamically generated
            and enum_class.__name__ not in ["UnwantedDirs", "UnwantedFiles"]
        ):
            for member in enum_class:
                members.append(member)
    return members


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
    "str_enum_member",
    _get_str_enum_members(),
    ids=lambda member: f"{member.__class__.__name__}.{member.name}",
)
def test_strenum_members_in_use(str_enum_member: StrEnum):
    enum_class_name = str_enum_member.__class__.__name__
    member_name = str_enum_member.name

    found = False
    unnecessary_value_usage = False

    for py_file in modules_to_test():
        file_found, file_unnecessary = _find_enum_usage_in_file(
            py_file, enum_class_name, member_name
        )
        if file_found:
            found = True
        if file_unnecessary:
            unnecessary_value_usage = True

    # Special case for TabStr members that might be used indirectly through Id enum
    if not found and enum_class_name == "TabStr":
        tab_to_id_mapping = {
            "init_tab": "init",
            "log_tab": "doctor",
            "apply_tab": "apply",
            "re_add_tab": "re_add",
            "add_tab": "add",
        }
        if member_name in tab_to_id_mapping:
            id_member_name = tab_to_id_mapping[member_name]
            for py_file in modules_to_test():
                file_found, _ = _find_enum_usage_in_file(
                    py_file, "Id", id_member_name
                )
                if file_found:
                    found = True
                    break

    if not found:
        pytest.fail(f"\n{member_name} from {enum_class_name} not in use.")

    elif unnecessary_value_usage:
        pytest.fail(
            f"\n{member_name} from {enum_class_name}: uses unnecessary .value attribute."
        )


def _get_enum_members() -> list[Enum]:
    members: list[Enum] = []
    for _, enum_class in inspect.getmembers(id_typing, inspect.isclass):
        if (
            issubclass(enum_class, Enum)
            and not issubclass(enum_class, StrEnum)
            and enum_class is not Enum  # exclude the Enum base class itself
            # exclude PwMgrInfo members since they are dynamically generated
            and enum_class.__name__ != "PwMgrInfo"
        ):
            for member in enum_class:
                members.append(member)
    return members


@pytest.mark.parametrize(
    "enum_member",
    _get_enum_members(),
    ids=lambda member: f"{member.__class__.__name__}.{member.name}",
)
def test_enum_members_in_use(enum_member: Enum):
    enum_class_name = enum_member.__class__.__name__
    member_name = enum_member.name

    found = False
    for py_file in modules_to_test():
        file_found, _ = _find_enum_usage_in_file(
            py_file, enum_class_name, member_name
        )
        if file_found:
            found = True
            break

    if not found:
        pytest.fail(f"\n{member_name} from {enum_class_name} not in use.")
