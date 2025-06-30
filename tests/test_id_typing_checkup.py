"""Test to check if all methods from the IdMixin are in use by modules in the src dir."""

import ast
import inspect
from functools import lru_cache

import pytest

from chezmoi_mousse.id_typing import IdMixin
from tests._test_utils import get_modules_to_test


class MethodCallVisitor(ast.NodeVisitor):
    """AST visitor to find method calls on objects that might inherit from IdMixin."""

    def __init__(self):
        self.method_calls: set[str] = set()

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Visit attribute access nodes to find method calls."""
        # Check if this is a method call (attribute access followed by a call)
        if isinstance(node.ctx, ast.Load):
            self.method_calls.add(node.attr)
        self.generic_visit(node)


@lru_cache(maxsize=1)
def get_idmixin_methods() -> set[str]:
    """Get all method names from the IdMixin class (excluding __init__)."""
    methods: set[str] = set()
    for name, _ in inspect.getmembers(IdMixin, predicate=inspect.isfunction):
        if not name.startswith("__"):  # Exclude special methods like __init__
            methods.add(name)
    return methods


@lru_cache(maxsize=1)
def get_method_calls_from_source() -> set[str]:
    """Extract all method calls from Python files in src/chezmoi_mousse directory."""
    modules_to_test = get_modules_to_test()
    all_method_calls: set[str] = set()

    for py_file in modules_to_test:
        try:
            with open(py_file, "r", encoding="utf-8") as file:
                content = file.read()

            tree = ast.parse(content, filename=str(py_file))
            visitor = MethodCallVisitor()
            visitor.visit(tree)
            all_method_calls.update(visitor.method_calls)

        except (SyntaxError, UnicodeDecodeError) as e:
            pytest.fail(f"Error parsing {py_file}: {e}")

    return all_method_calls


def test_all_idmixin_methods_are_used():
    """Test that all IdMixin methods are being called somewhere in the codebase."""
    idmixin_methods = get_idmixin_methods()
    source_method_calls = get_method_calls_from_source()
    unused_methods = idmixin_methods - source_method_calls

    assert (
        len(unused_methods) == 0
    ), f"The following IdMixin methods are not being used: {sorted(unused_methods)}"


def test_idmixin_method_parameter_types():

    # Check method signatures for expected parameter types
    method_signatures: dict[str, inspect.Signature] = {}
    for name, method in inspect.getmembers(
        IdMixin, predicate=inspect.isfunction
    ):
        if not name.startswith("__"):
            sig = inspect.signature(method)
            method_signatures[name] = sig

    # Verify that key enum types are being used in method parameters
    expected_parameter_types = {
        "ButtonEnum",
        "Location",
        "FilterEnum",
        "TreeStr",
        "ViewStr",
    }

    all_parameter_annotations: set[str] = set()
    for name, sig in method_signatures.items():
        for param_name, param in sig.parameters.items():
            if (
                param_name != "self"
                and param.annotation != inspect.Parameter.empty
            ):
                # Extract type name from annotation
                if hasattr(param.annotation, "__name__"):
                    all_parameter_annotations.add(param.annotation.__name__)
                else:
                    # Handle more complex annotations like Union, etc.
                    all_parameter_annotations.add(str(param.annotation))

    # Check that expected enum types are being used
    used_expected_types = expected_parameter_types.intersection(
        all_parameter_annotations
    )

    # This test passes if we find some expected parameter types
    assert (
        len(used_expected_types) > 0
    ), "No expected enum parameter types found in IdMixin methods"
