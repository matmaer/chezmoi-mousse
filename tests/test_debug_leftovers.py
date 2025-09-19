import ast
from pathlib import Path

import pytest
from _test_utils import modules_to_test

exclude_files = ["__init__.py"]


class DebugStatementVisitor(ast.NodeVisitor):

    def __init__(self) -> None:
        self.debug_statements: list[str] = []

    # This method is called for EVERY function call in the code
    def visit_Call(self, node: ast.Call) -> None:
        # Check for print() calls
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            self.debug_statements.append(f"print() call at line {node.lineno}")

        # Check for debug_log.some_method() calls
        elif isinstance(node.func, ast.Attribute):
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "debug_log"
            ):
                self.debug_statements.append(
                    f"debug_log.{node.func.attr}() call at line {node.lineno}"
                )

            # Check for self.chezmoi.debug_log.some_method() calls
            elif (
                isinstance(node.func.value, ast.Attribute)
                and isinstance(node.func.value.value, ast.Attribute)
                and isinstance(node.func.value.value.value, ast.Name)
                and node.func.value.value.value.id == "self"
                and node.func.value.value.attr == "chezmoi"
                and node.func.value.attr == "debug_log"
            ):
                self.debug_statements.append(
                    f"self.chezmoi.debug_log.{node.func.attr}() call at line {node.lineno}"
                )

            # Check for self.app.chezmoi.debug_log.some_method() calls
            elif (
                isinstance(node.func.value, ast.Attribute)
                and isinstance(node.func.value.value, ast.Attribute)
                and isinstance(node.func.value.value.value, ast.Attribute)
                and isinstance(node.func.value.value.value.value, ast.Name)
                and node.func.value.value.value.value.id == "self"
                and node.func.value.value.value.attr == "app"
                and node.func.value.value.attr == "chezmoi"
                and node.func.value.attr == "debug_log"
            ):
                self.debug_statements.append(
                    f"self.app.chezmoi.debug_log.{node.func.attr}() call at line {node.lineno}"
                )

        # Call this to continue traversing child nodes recursively
        # Without generic_visit - misses nested calls
        self.generic_visit(node)


@pytest.mark.parametrize(
    "py_file",
    modules_to_test(exclude_file_names=exclude_files),
    ids=lambda py_file: py_file.name,
)
def test_leftovers(py_file: Path) -> None:

    content = py_file.read_text()
    tree = ast.parse(content)

    visitor = DebugStatementVisitor()
    visitor.visit(tree)

    if visitor.debug_statements:
        statements_found = "\n".join(visitor.debug_statements)
        pytest.fail(
            f"Debug statements found in {py_file.name}:\n{statements_found}"
        )
