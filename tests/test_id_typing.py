"""Test to check if all methods from the IdMixin are in use by modules in the src dir."""

import ast
import inspect

import pytest

from chezmoi_mousse.id_typing import IdMixin
from _test_utils import get_modules_to_test


def get_method_calls_from_modules_to_test() -> set[str]:
    all_method_calls: set[str] = set()

    for py_file in get_modules_to_test():
        try:
            content = py_file.read_text()
            tree = ast.parse(content, filename=str(py_file))
            method_calls = {
                node.attr
                for node in ast.walk(tree)
                if isinstance(node, ast.Attribute)
                and isinstance(node.ctx, ast.Load)
            }
            all_method_calls.update(method_calls)
        except (SyntaxError, UnicodeDecodeError) as e:
            pytest.fail(f"Error parsing {py_file}: {e}")

    return all_method_calls


def test_all_idmixin_methods_are_used():
    idmixin_methods = {
        name
        for name, _ in inspect.getmembers(
            IdMixin, predicate=inspect.isfunction
        )
        if name != "__init__"
    }
    source_method_calls = get_method_calls_from_modules_to_test()
    unused_methods = idmixin_methods - source_method_calls

    assert (
        len(unused_methods) == 0
    ), f"IdMixin methods not in use: {len(unused_methods)}\n" + "\n".join(
        sorted(unused_methods)
    )
