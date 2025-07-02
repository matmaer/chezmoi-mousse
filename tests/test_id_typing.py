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


def test_no_hardcoded_ids():
    violations: list[str] = []

    for py_file in get_modules_to_test():
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
                            f'{py_file.name}:{keyword.lineno} - id="{keyword.value.value}"'
                        )

    if violations:
        print(f"\nFound {len(violations)} hardcoded IDs:")
        for violation in violations:
            print(f"  {violation}")
        print(
            "\nIDs should be generated using IdMixin methods instead of hardcoded strings."
        )
        assert (
            False
        ), f"Found {len(violations)} hardcoded IDs (see details above)"
