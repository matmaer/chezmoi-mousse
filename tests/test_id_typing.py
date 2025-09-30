"""Test if all Enum members from id_typing.py are in use."""

import ast

import pytest
from _test_utils import get_module_paths

import chezmoi_mousse.id_typing as id_typing


def _get_class_public_members_strings(
    class_object: type,
) -> list[tuple[str, str]]:
    members: list[tuple[str, str]] = []
    for name in dir(class_object):
        if not name.startswith("_"):
            attr = getattr(class_object, name)
            if isinstance(attr, property):
                members.append((name, "property"))
            elif callable(attr):  # This catches all callable types
                members.append((name, "method"))
            else:
                members.append((name, "attribute"))
    return members


@pytest.mark.parametrize(
    "member_name, member_type",
    _get_class_public_members_strings(id_typing.TabIds),
    ids=[
        name for name, _ in _get_class_public_members_strings(id_typing.TabIds)
    ],
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
    _get_class_public_members_strings(id_typing.ScreenIds),
    ids=[
        name
        for name, _ in _get_class_public_members_strings(id_typing.ScreenIds)
    ],
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
    "member_name, member_type",
    _get_class_public_members_strings(id_typing.Id),
    ids=[name for name, _ in _get_class_public_members_strings(id_typing.Id)],
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
