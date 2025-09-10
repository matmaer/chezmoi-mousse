"""Test if all methods from the IdMixin are in use by modules in the src dir."""

import ast
from pathlib import Path

import pytest
from _test_utils import modules_to_test


@pytest.mark.parametrize(
    "py_file",
    modules_to_test(
        exclude_file_names=[
            "__init__.py",
            "__main__.py",
            "custom_theme.py",
            "overrides.py",
        ]
    ),
    ids=lambda py_file: py_file.name,
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
