"""Test to check if all methods from the IdMixin are in use by modules in the src dir."""

import ast
import inspect

import pytest

from chezmoi_mousse.id_typing import IdMixin
from _test_utils import get_modules_to_test


def extract_method_calls(tree: ast.AST) -> set[str]:
    # extract all method calls from an AST tree
    method_calls: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
            method_calls.add(node.attr)

    return method_calls


def get_idmixin_methods() -> set[str]:
    # get all method names from the IdMixin class (excluding __init__)
    return {
        name
        for name, _ in inspect.getmembers(
            IdMixin, predicate=inspect.isfunction
        )
        if name != "__init__"
    }


def get_method_calls_from_modules_to_test() -> set[str]:
    all_method_calls: set[str] = set()

    for py_file in get_modules_to_test():
        try:
            content = py_file.read_text()
            tree = ast.parse(content, filename=str(py_file))
            method_calls = extract_method_calls(tree)
            all_method_calls.update(method_calls)
        except (SyntaxError, UnicodeDecodeError) as e:
            pytest.fail(f"Error parsing {py_file}: {e}")

    return all_method_calls


def test_all_idmixin_methods_are_used():
    """Test that all IdMixin methods are being used in the codebase."""
    idmixin_methods = get_idmixin_methods()
    source_method_calls = get_method_calls_from_modules_to_test()
    unused_methods = idmixin_methods - source_method_calls

    assert (
        len(unused_methods) == 0
    ), f"IdMixin methods not in use: {len(unused_methods)}\n" + "\n".join(
        sorted(unused_methods)
    )
