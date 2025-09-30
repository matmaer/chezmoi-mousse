"""Test if all Enum members from id_typing.py are in use."""

import ast
import inspect
from enum import Enum

import pytest
from _test_utils import (
    find_dataclass_field_usage,
    find_enum_usage_in_file,
    get_class_public_members_strings,
    get_dataclass_fields,
    get_dataclasses_from_module,
    get_module_paths,
)

import chezmoi_mousse.id_typing as id_typing


def _get_enum_members() -> list[Enum]:
    members: list[Enum] = []
    for _, enum_class in inspect.getmembers(id_typing, inspect.isclass):
        if (
            issubclass(enum_class, Enum)
            # exclude PwMgrInfo members since they are dynamically generated
            and enum_class.__name__ != "PwMgrInfo"
            # exclude classes that are imported from other modules
            and enum_class.__module__ == "chezmoi_mousse.id_typing"
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
    for py_file in get_module_paths(exclude_file_names=["custom_theme.py"]):
        file_found, _ = find_enum_usage_in_file(
            py_file, enum_class_name, member_name
        )
        if file_found:
            found = True
            break

    if not found:
        pytest.fail(f"\n{member_name} from {enum_class_name} not in use.")


@pytest.mark.parametrize(
    "member_name, member_type",
    get_class_public_members_strings(id_typing.TabIds),
)
def test_tabids_member_in_use(member_name: str, member_type: str):
    is_used = False

    for py_file in get_module_paths(exclude_file_names=["id_typing.py"]):
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
    "member_name, member_type",
    get_class_public_members_strings(id_typing.ScreenIds),
)
def test_screen_ids_member_in_use(member_name: str, member_type: str):
    is_used = False

    for py_file in get_module_paths(exclude_file_names=["id_typing.py"]):
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
    "member_name, member_type", get_class_public_members_strings(id_typing.Id)
)
def test_id_members_in_use(member_name: str, member_type: str):
    is_used = False

    for py_file in get_module_paths(exclude_file_names=["id_typing.py"]):
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


def _get_dataclass_field_params() -> list[tuple[str, str, str]]:
    """Get all dataclass fields as test parameters."""
    params: list[tuple[str, str, str]] = []
    dataclasses = get_dataclasses_from_module(id_typing)

    for dataclass_type in dataclasses:
        fields = get_dataclass_fields(dataclass_type)
        for field_name, field_type in fields:
            params.append((dataclass_type.__name__, field_name, field_type))

    return params


@pytest.mark.parametrize(
    "dataclass_name,field_name,field_type",
    _get_dataclass_field_params(),
    ids=lambda param: (
        f"{param[0]}.{param[1]}" if isinstance(param, tuple) else str(param)
    ),
)
def test_dataclass_fields_in_use(
    dataclass_name: str, field_name: str, field_type: str
):
    """Test that all dataclass fields are accessed somewhere in the codebase."""
    found = False

    for py_file in get_module_paths(exclude_file_names=["id_typing.py"]):
        # only test public fields
        if field_name.startswith("_"):
            return
        if find_dataclass_field_usage(py_file, dataclass_name, field_name):
            found = True
            break

    if not found:
        pytest.fail(
            f"\n{dataclass_name}.{field_name} ({field_type}) not in use."
        )
