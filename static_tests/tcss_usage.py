from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse.str_enums import Tcss

if TYPE_CHECKING:
    from static_tests._ast_nodes import NodeDb
    from static_tests.conftest import CheckRunner, IssueList

TCSS_PATH = Path("src", "chezmoi_mousse", "gui", "gui.tcss")

EXCLUDE_TCSS_CLASSES = {"-visible"}


def _load_tcss_content() -> tuple[list[str], str]:
    """Reads TCSS file content excluding comment lines."""
    if not TCSS_PATH.exists():
        return [], ""

    raw_lines = TCSS_PATH.read_text(encoding="utf-8").splitlines()
    clean_lines = [
        line for line in raw_lines if not line.strip().startswith(("/", "*", "#"))
    ]
    return clean_lines, "\n".join(clean_lines)


def _extract_tcss_classes(tcss_content: str) -> set[str]:
    """Extracts all class selectors (e.g. `.flat_button`) from TCSS."""
    pattern = r"\.([a-zA-Z0-9_-]+)/b"
    matches = re.findall(pattern, tcss_content)
    return {m for m in matches if m not in EXCLUDE_TCSS_CLASSES and "--" not in m}


def _extract_type_selectors(tcss_lines: list[str]) -> set[str]:
    """Extracts PascalCase type selectors (e.g. `ManagedTree`) from TCSS rules."""
    pattern = r"\b([A-Z][A-Za-z]+)\b"
    matches: set[str] = set()
    for line in tcss_lines:
        # Ignore comments or color variable definitions
        if "$" in line or (":" in line and not line.strip().endswith("{")):
            continue
        matches.update(re.findall(pattern, line))
    return matches


def _valid_tcss_type_selectors(node_db: NodeDb) -> set[str]:
    # Local python classes + Textual framework subclasses plus some exceptions
    # that we don't import but target
    valid_python_classes = {
        data.ast_node.name
        for data in node_db.by_type.get(ast.ClassDef.__name__, set())
        if isinstance(data.ast_node, ast.ClassDef)
    }
    return (
        valid_python_classes
        | node_db.textual_imports
        | {"CollapsibleTitle", "Contents", "Tab", "ToggleButton"}
    )


# --- Static Check Functions ---


def check_tcss_classes_in_enum(node_db: NodeDb) -> IssueList:
    """Checks that all TCSS classes used in gui.tcss exist in the Tcss StrEnum."""
    _ = node_db
    _, tcss_content = _load_tcss_content()
    if not tcss_content:
        return []

    tcss_enum_members = {member.value for member in Tcss}
    used_classes = _extract_tcss_classes(tcss_content)

    issues: IssueList = []
    for cls_name in sorted(used_classes):
        if cls_name not in tcss_enum_members:
            issues.append(
                (f".{cls_name}", "gui.tcss", "TCSS class not defined in Tcss StrEnum")
            )

    return issues


def check_tcss_type_selectors(node_db: NodeDb) -> IssueList:
    tcss_lines, _ = _load_tcss_content()
    if not tcss_lines:
        return []

    used_selectors = _extract_type_selectors(tcss_lines)
    issues: IssueList = []

    for selector in sorted(used_selectors):
        if selector not in _valid_tcss_type_selectors(node_db):
            issues.append(
                (
                    selector,
                    "gui.tcss",
                    "TCSS type selector does not match any known Python class",
                )
            )

    return issues


def check_hardcoded_tcss_strings(node_db: NodeDb) -> IssueList:
    issues: IssueList = []
    call_nodes = node_db.by_type.get(ast.Call.__name__, set())

    for node_data in call_nodes:
        assert isinstance(node_data.ast_node, ast.Call)
        call = node_data.ast_node

        # 1. Check keyword arguments: Widget(..., classes="hardcoded")
        for kw in call.keywords:
            if kw.arg == "classes":
                _validate_tcss_expr(
                    kw.value, node_data.rel_path, node_data.lineno, issues
                )

        # 2. Check method calls: widget.add_class("hardcoded")
        if (
            isinstance(call.func, ast.Attribute)
            and call.func.attr == "add_class"
            and call.args
        ):
            _validate_tcss_expr(
                call.args[0], node_data.rel_path, node_data.lineno, issues
            )

    return issues


def _validate_tcss_expr(
    expr: ast.expr, rel_path: str, lineno: int | None, issues: IssueList
) -> None:
    loc = f"{rel_path}:{lineno or 0}"
    # temporary exception for DIFF_TCSS member lookup from the dict, e.g.
    # widgets.append(
    #     Static(text, classes=DIFF_TCSS[prefix].value, markup=False) ...
    # )...
    if (
        isinstance(expr, ast.Attribute)
        and isinstance(expr.value, ast.Subscript)
        and isinstance(expr.value.value, ast.Name)
        and expr.value.value.id == "DIFF_TCSS"
    ):
        return

    # Flag string literals directly: classes="flat_button"
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        if expr.value not in EXCLUDE_TCSS_CLASSES:
            issues.append(
                (
                    ast.unparse(expr),
                    loc,
                    "Hardcoded string literal used instead of Tcss enum",
                )
            )

    # Allow Tcss.member attribute lookups, flag other dynamic/f-string expressions
    elif not (
        isinstance(expr, ast.Attribute)
        and isinstance(expr.value, ast.Name)
        and expr.value.id == "Tcss"
    ):
        issues.append(
            (
                ast.unparse(expr),
                loc,
                "Expression should be a Tcss enum member",
            )
        )


def get_tcss_issues(node_db: NodeDb) -> IssueList:
    issues: IssueList = []
    issues.extend(check_tcss_classes_in_enum(node_db))
    issues.extend(check_tcss_type_selectors(node_db))
    issues.extend(check_hardcoded_tcss_strings(node_db))
    return issues


def test_tcss(run_check: CheckRunner) -> None:
    run_check(get_tcss_issues)
