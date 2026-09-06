import pytest
from static_tests._ast_nodes import NodeDb

# TODO: debug log calls


def test_print_calls(node_db: NodeDb) -> None:
    print_nodes = node_db.by_name.get("print", set())
    issues: set[str] = set()
    for data in print_nodes:
        issues.add(f"print call in {data.rel_path}:{data.lineno}")

    if issues:
        msg = f"{len(issues)} debug leftovers:\n\n" + "\n".join(sorted(issues))
        pytest.fail(msg, pytrace=False)
