import ast
from pathlib import Path

import pytest


class QueryOneCallDetector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.current_file: str = ""
        self.issues: list[str] = []

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute) and node.func.attr == "query_one":

            first_arg = node.args[0]
            first_arg_str: str = ""

            if isinstance(first_arg, ast.Constant):
                # String literal like "MyClass"
                if isinstance(first_arg.value, str):
                    first_arg_str = first_arg.value
                else:
                    first_arg_str = str(first_arg.value)
            elif isinstance(first_arg, ast.Name):
                # Variable/class name like my_var
                first_arg_str = first_arg.id
            elif isinstance(first_arg, ast.Attribute):
                # Attribute like ids.container.pre_operate
                first_arg_str = first_arg.attr
            else:
                self.issues.append(
                    f"Cannot determine first argument type "
                    f"({self.current_file}:{node.lineno})"
                )
                self.generic_visit(node)
                return

            if not first_arg_str.endswith("_q"):
                self.issues.append(
                    f"'{first_arg_str}' not ending with '_q' "
                    f"({self.current_file}:{node.lineno})"
                )

        # Continue walking down the tree (e.g., nested calls)
        self.generic_visit(node)


def test_query_one_calls() -> None:
    detector = QueryOneCallDetector()
    src_dir = Path(__file__).parent.parent / "src"
    py_files = list(src_dir.rglob("*.py"))

    # Collect all query_one argument issues across modules
    for file_path in py_files:
        detector.current_file = str(file_path.relative_to(src_dir.parent))
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        detector.visit(tree)

    if detector.issues:
        error_message = "\nFound query_one calls with issues:\n" + "\n".join(
            detector.issues
        )
        pytest.fail(error_message)
