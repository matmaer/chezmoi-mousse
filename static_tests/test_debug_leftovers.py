import ast
from dataclasses import dataclass
from pathlib import Path

import pytest
from _test_utils import get_module_ast_tree, get_module_paths


@dataclass
class DebugStatement:
    file_path: Path
    class_name: str | None
    line_number: int


class DebugStatementVisitor(ast.NodeVisitor):

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.debug_statements: list[DebugStatement] = []
        self.class_stack: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    # This method is called for EVERY function call in the code
    def visit_Call(self, node: ast.Call) -> None:
        class_name = self.class_stack[-1] if self.class_stack else None

        # Check for print() calls
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            self.debug_statements.append(
                DebugStatement(self.file_path, class_name, node.lineno)
            )

        # Check for debug_log.some_method() calls
        elif isinstance(node.func, ast.Attribute) and (
            isinstance(node.func.value, ast.Name)
            and node.func.value.id == "debug_log"
            or isinstance(node.func.value, ast.Attribute)
            and node.func.value.attr == "debug_log"
        ):
            self.debug_statements.append(
                DebugStatement(self.file_path, class_name, node.lineno)
            )


@pytest.mark.parametrize("py_file", get_module_paths(), ids=lambda p: p.name)
def test_leftovers(py_file: Path) -> None:
    visitor = DebugStatementVisitor(py_file)
    visitor.visit(get_module_ast_tree(py_file))

    if visitor.debug_statements:
        messages: list[str] = []
        for result in visitor.debug_statements:
            class_part = result.class_name if result.class_name else "module"
            messages.append(
                f"{result.file_path.name}: {class_part}: line {result.line_number}"
            )
        pytest.fail("Debug statements found:\n" + "\n".join(messages))
