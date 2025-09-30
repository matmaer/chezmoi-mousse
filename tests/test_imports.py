"""Test that modules don't import from _str_enums.py."""

import ast
from pathlib import Path

import pytest
from _test_utils import get_module_paths


@pytest.mark.parametrize(
    "py_file",
    get_module_paths(exclude_file_names=["id_typing.py"]),
    ids=lambda py_file: py_file.name,
)
def test_from_str_enums_module(py_file: Path) -> None:
    tree = ast.parse(py_file.read_text())
    results: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "chezmoi_mousse._str_enums"
        ):
            for alias in node.names:
                results.append(
                    f"{py_file.name} imports {alias.name} from _str_enums.py"
                )
    if results:
        pytest.fail("\n".join(results))
