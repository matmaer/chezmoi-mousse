import pytest
from static_tests._ast_nodes import NodeDb, format_issues


def get_print_calls(node_db: NodeDb) -> list[tuple[str, str, str]]:
    issues_set: set[tuple[str, str, str]] = set()
    print_nodes = node_db.by_name.get("print", set())
    for data in print_nodes:
        issues_set.add(("print", f"{data.rel_path}:{data.lineno}", "Call(s) to print"))
    return list(issues_set)


def test_print_calls(node_db: NodeDb) -> None:
    issues = get_print_calls(node_db)
    if issues:
        pytest.fail(format_issues(issues))
