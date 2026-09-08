from static_tests._ast_nodes import NodeDb
from static_tests.conftest import CheckRunner, IssueList


def get_print_calls(node_db: NodeDb) -> IssueList:
    issues_set: set[tuple[str, ...]] = set()
    print_nodes = node_db.by_name.get("print", set())
    for data in print_nodes:
        issues_set.add(
            (
                f"{data.rel_path}:{data.lineno}",
                "Call(s) to print",
            )
        )
    return list(issues_set)


def test_print_calls(run_check: CheckRunner) -> None:
    run_check(get_print_calls)
