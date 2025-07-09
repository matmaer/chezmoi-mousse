"""Test if all methods from the IdMixin are in use by modules in the src dir."""

import ast
from pathlib import Path

import pytest
from _test_utils import modules_to_test


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


# TODO: implement checkup of StrEnum and Enum member usage


# import inspect
# from enum import Enum, StrEnum
# from pathlib import Path


# import chezmoi_mousse.id_typing as id_typing


# def all_id_typing_enum_classes() -> list[str]:
#     return [
#         name
#         for name, cls in inspect.getmembers(id_typing, inspect.isclass)
#         if issubclass(cls, Enum)
#     ]


# def id_typing_all_str_enum_classes() -> list[str]:
#     return [
#         name
#         for name, cls in inspect.getmembers(id_typing, inspect.isclass)
#         if issubclass(cls, StrEnum)
#     ]
