"""Test if all methods from the IdMixin are in use by modules in the src dir."""

import ast
import inspect
from enum import StrEnum
from pathlib import Path

import pytest
from _test_utils import modules_to_test

import chezmoi_mousse.id_typing as id_typing


@pytest.mark.parametrize(
    "py_file", modules_to_test(), ids=lambda py_file: py_file.name
)
def test_no_hardcoded_ids(py_file: Path):
    violations: list[str] = []

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
                    violations.append(
                        f'Line {keyword.lineno}: id="{keyword.value.value}"'
                    )

    if violations:
        violation_details = "\n  ".join(violations)
        pytest.fail(
            f"Found {len(violations)} hardcoded ID(s) in {py_file.name}:\n"
            f"  {violation_details}\n\n"
            f"IDs should be generated using IdMixin methods instead of hardcoded strings."
        )


def get_str_enum_members() -> list[StrEnum]:
    """Helper to get all members of all StrEnum classes in id_typing."""
    members: list[StrEnum] = []
    for _, enum_class in inspect.getmembers(id_typing, inspect.isclass):
        if issubclass(enum_class, StrEnum) and enum_class is not StrEnum:
            for member in enum_class:
                members.append(member)
    return members


@pytest.mark.parametrize(
    "str_enum_member",
    get_str_enum_members(),
    ids=lambda member: f"{member.__class__.__name__}.{member.name}",
)
def test_str_enum_members_in_use(str_enum_member: StrEnum):
    """Check if a StrEnum member is used in any of the source files."""
    search_term = str(str_enum_member.value)
    found = False
    for py_file in modules_to_test(exclude_file_names=["id_typing.py"]):
        content = py_file.read_text()
        if search_term in content:
            found = True
            break

    if not found:
        pytest.skip(
            f"'{str_enum_member.name}' from {str_enum_member.__class__.__name__} "
            "is not in use."
        )
