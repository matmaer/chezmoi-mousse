import ast
from pathlib import Path

import pytest

from static_tests._cached_data import MODULE_DIR, ast_parse, get_file_paths


class DebugStatementDetector(ast.NodeVisitor):

    def __init__(self) -> None:
        self.current_file: str = ""
        self.class_stack: list[str] = []
        # Store leaks as tuples: (file_path_str, class_or_module, line_number)
        self.debug_statements: list[tuple[str, str, int]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        # Determine context (class name or "module")
        context = self.class_stack[-1] if self.class_stack else "module"

        # Check for print(...)
        is_print = isinstance(node.func, ast.Name) and node.func.id == "print"

        # Check for debug_log(...) or obj.debug_log(...)
        is_debug_log = isinstance(node.func, ast.Attribute) and (
            (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "debug_log"
            )
            or (
                isinstance(node.func.value, ast.Attribute)
                and node.func.value.attr == "debug_log"
            )
        )

        # Skip print statements inside main.py entirely
        if is_print and Path(self.current_file).name == "main.py":
            return

        if is_print or is_debug_log:
            self.debug_statements.append((self.current_file, context, node.lineno))

        self.generic_visit(node)


def test_leftovers() -> None:
    detector = DebugStatementDetector()

    for file_path in get_file_paths():
        detector.current_file = str(file_path.relative_to(MODULE_DIR))
        tree = ast_parse(file_path)
        detector.visit(tree)

    if detector.debug_statements:
        messages: list[str] = []
        for file, context, line in detector.debug_statements:
            messages.append(f"{file}: {context}: line {line}")

        pytest.fail("Debug statements found:\n" + "\n".join(messages))
