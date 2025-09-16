"""Test if all Enum members from id_typing.py are in use."""

import ast
import inspect
from enum import Enum, StrEnum

import pytest
from _test_utils import (
    find_enum_usage_in_file,
    get_class_public_members,
    modules_to_test,
)

import chezmoi_mousse.id_typing as id_typing


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
    for py_file in modules_to_test(
        exclude_file_names=[
            "__init__.py",
            "__main__.py",
            "custom_theme.py",
            "overrides.py",
        ]
    ):
        file_found, _ = find_enum_usage_in_file(
            py_file, enum_class_name, member_name
        )
        if file_found:
            found = True
            break

    if not found:
        pytest.fail(f"\n{member_name} from {enum_class_name} not in use.")


@pytest.mark.parametrize(
    "member_name, member_type", get_class_public_members(id_typing.TabIds)
)
def test_tabids_member_in_use(member_name: str, member_type: str):
    is_used = False

    for py_file in modules_to_test(exclude_file_names=["id_typing.py"]):
        content = py_file.read_text()
        tree = ast.parse(content, filename=str(py_file))

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == member_name:
                is_used = True
                break  # Found usage
        if is_used:
            break  # No need to check other files

    if not is_used:
        pytest.fail(f"\nNot in use: {member_name} {member_type}")


@pytest.mark.parametrize(
    "member_name, member_type", get_class_public_members(id_typing.ScreenIds)
)
def test_screen_ids_member_in_use(member_name: str, member_type: str):
    is_used = False

    for py_file in modules_to_test(exclude_file_names=["id_typing.py"]):
        content = py_file.read_text()
        tree = ast.parse(content, filename=str(py_file))

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == member_name:
                is_used = True
                break  # Found usage
        if is_used:
            break  # No need to check other files

    if not is_used:
        pytest.fail(f"\nNot in use: {member_name} {member_type}")


@pytest.mark.parametrize(
    "member_name, member_type", get_class_public_members(id_typing.Id)
)
def test_id_member_in_use(member_name: str, member_type: str):
    is_used = False

    for py_file in modules_to_test(exclude_file_names=["id_typing.py"]):
        content = py_file.read_text()
        tree = ast.parse(content, filename=str(py_file))

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == member_name:
                is_used = True
                break  # Found usage
        if is_used:
            break  # No need to check other files

    if not is_used:
        pytest.fail(f"\nNot in use: {member_name} {member_type}")
