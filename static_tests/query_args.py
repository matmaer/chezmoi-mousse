import ast
import re

import pytest
from static_tests._ast_nodes import NodeDb

QUERY_ONE = "query_one"
QUERY_EXACTLY_ONE = "query_exactly_one"


def looks_like_class_name(s: str) -> bool:
    return bool(re.fullmatch(r"[A-Z][A-Za-z]*[a-z]", s))


def check_valid_select_type(arg: ast.expr) -> str | None:
    """
    Allowed:
    - SomeClass (ast.Name.id, starting uppercase
    - SomeClass.SomeSubclass (ast.Attribute.attr, SomeSubClass starting uppercase)
    """
    valid = False
    if isinstance(arg, ast.Name):
        valid = bool(re.fullmatch(r"[A-Z][A-Za-z]*[a-z]", arg.id))
    elif isinstance(arg, ast.Attribute):
        valid = bool(re.fullmatch(r"[A-Z][A-Za-z]*[a-z]", arg.attr))
    if not valid:
        return "unexpected select type"
    return None


def check_query_call(call_node: ast.Call, func_name: str) -> str | None:
    """These are self imposed rules for housekeeping, not always requirements for valid
    textual query arguments."""
    reason: str | None = None

    if func_name == QUERY_EXACTLY_ONE:
        if len(call_node.args) != 1:
            reason = f"expected 1 arg, got {len(call_node.args)}"
        else:
            reason = check_valid_select_type(call_node.args[0])
    elif func_name == QUERY_ONE:
        if len(call_node.args) != 2:
            reason = "expected id and select type"
        else:
            selector_arg, select_type = call_node.args[0], call_node.args[1]
            if not isinstance(
                selector_arg, ast.Attribute
            ) or not selector_arg.attr.endswith("_q"):
                reason = "id is not a dotted lookup ending in '_q'"
            else:
                reason = check_valid_select_type(select_type)
    return reason


def test_query_args(node_db: NodeDb) -> None:
    q_one_nodes = node_db.by_name.get(QUERY_ONE, set())
    q_exactly_one_nodes = node_db.by_name.get(QUERY_EXACTLY_ONE, set())

    issues: list[str] = []

    for data in q_one_nodes | q_exactly_one_nodes:
        if not isinstance(data.ast_node, ast.Call) or not isinstance(data.str_rep, str):
            continue

        node_str = ast.unparse(data.ast_node)
        reason = check_query_call(data.ast_node, data.str_rep)
        if reason is None:
            continue
        issues.append(f"{node_str} {reason} ({data.rel_path}:{data.lineno})")

    if issues:
        issues.sort()
        msg = f"{len(issues)} invalid query calls:\n\n" + "\n".join(issues)
        pytest.fail(msg)
