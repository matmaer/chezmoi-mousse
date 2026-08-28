import ast
from collections.abc import Callable
from pathlib import Path


class QueryOneCallRule:
    def __init__(self) -> None:
        self.nodes_to_check: dict[Path, list[ast.Call]] = {}

    # Accept ast.AST to satisfy ErrorRule Protocol
    def get_rule_data(self, file_path: Path, node: ast.AST) -> None:
        # Filter for ast.Call and query_one or query_exactly_one
        if isinstance(node, ast.Call) and (
            getattr(node.func, "id", None) == "query_one"
            or getattr(node.func, "attr", None) == "query_exactly_one"
        ):
            self.nodes_to_check.setdefault(file_path, []).append(node)

    def is_valid_call(self, call_node: ast.Call) -> tuple[str, bool]:
        func_name = None
        if isinstance(call_node.func, ast.Attribute):
            func_name = call_node.func.attr
        elif isinstance(call_node.func, ast.Name):
            func_name = call_node.func.id
        assert isinstance(func_name, str)
        # Common guard: exactly 1 positional arg, 0 keyword args, no constants
        if (
            len(call_node.args) != 1
            or call_node.keywords
            or isinstance(call_node.args[0], ast.Constant)
        ):
            return func_name, False

        full_arg_str: str = ast.unparse(call_node.args[0])
        parts = full_arg_str.split(".")

        if func_name == "query_one":
            return func_name, len(parts) > 1 and full_arg_str.endswith("_q")
        elif func_name == "query_exactly_one":
            return func_name, all(part.isupper() for part in parts)

        return func_name, full_arg_str.endswith("_q")

    def get_issues(self) -> list[str]:
        issues: list[tuple[str, str, Path, int]] = []
        for path, nodes in self.nodes_to_check.items():
            for node in nodes:
                func_name, is_valid = self.is_valid_call(node)
                if not is_valid:
                    issues.append((func_name, "invalid call", path, node.lineno))
        return sorted(
            f"{func_name}: {msg} ({path}:{lineno})"
            for func_name, msg, path, lineno in issues
        )


def test_query_one_usage(run_node_rule: Callable[..., list[str]]) -> None:
    run_node_rule(QueryOneCallRule())
