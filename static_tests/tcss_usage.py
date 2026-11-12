from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from chezmoi_mousse.str_enums import Tcss

if TYPE_CHECKING:
    from static_tests._ast_nodes import NodeDb


EXCLUDE_TCSS_CLASSES = {"-visible"}
ADDITIONAL_TYPE_SELECTORS = {"Contents", "Tab", "Toast"}


class GuiTcss:
    def __init__(self) -> None:
        self.path = Path("src", "chezmoi_mousse", "gui", "gui.tcss")
        self.lines: list[str] = self._get_relevant_tcss_lines(self.path)
        self.class_selectors: set[str] = self._extract_tcss_classes(self.lines)
        self.type_selectors: set[str] = self._extract_type_selectors(self.lines)

    def _get_relevant_tcss_lines(self, tcss_path: Path) -> list[str]:
        raw_lines = tcss_path.read_text(encoding="utf-8").splitlines()
        return [
            line
            for line in raw_lines
            if line.strip()
            and not line.strip().startswith(("/", "*", "#"))
            and ";" not in line
            and "}" not in line
            and "--" not in line
        ]

    def _extract_tcss_classes(self, lines: list[str]) -> set[str]:
        text = " ".join(lines)
        # Extracts all class selectors (e.g. `.flat_button`)
        pattern = r"\.([a-zA-Z0-9_-]+)/b"
        matches = re.findall(pattern, text)
        return {m for m in matches if m not in EXCLUDE_TCSS_CLASSES}

    def _extract_type_selectors(self, lines: list[str]) -> set[str]:
        # Extracts PascalCase type selectors (e.g. `ManagedTree`)
        pattern = r"\b([A-Z][A-Za-z]+)\b"
        matches: set[str] = set()
        for line in lines:
            matches.update(re.findall(pattern, line))
        return matches


gui_tcss = GuiTcss()


def _valid_tcss_type_selectors(node_db: NodeDb) -> set[str]:
    # Local python classes + Textual framework subclasses plus some exceptions
    # that we don't import but target
    valid_python_classes = {
        data.ast_node.name
        for data in node_db.by_type.get(ast.ClassDef.__name__, set())
        if isinstance(data.ast_node, ast.ClassDef)
    }
    return valid_python_classes | node_db.textual_imports | ADDITIONAL_TYPE_SELECTORS


# --- Static Check Functions ---


def check_tcss_classes_in_enum() -> list[tuple[str, str, str]]:
    # check TCSS classes used in gui.tcss exist in the Tcss StrEnum

    tcss_enum_members = {member.value for member in Tcss}

    issues: list[tuple[str, str, str]] = []
    for cls_name in gui_tcss.class_selectors:
        if cls_name not in tcss_enum_members:
            issues.append(
                (f".{cls_name}", "gui.tcss", "TCSS class not defined in Tcss StrEnum")
            )

    return issues


def check_tcss_type_selectors(node_db: NodeDb) -> list[tuple[str, str, str]]:

    issues: list[tuple[str, str, str]] = []

    for selector in sorted(gui_tcss.class_selectors):
        if selector not in _valid_tcss_type_selectors(node_db):
            issues.append(
                (
                    selector,
                    "gui.tcss",
                    "TCSS type selector does not match any known Python class",
                )
            )

    return issues


def check_hardcoded_tcss_strings(node_db: NodeDb) -> list[tuple[str, str, str]]:
    issues: list[tuple[str, str, str]] = []
    call_nodes = node_db.by_type.get(ast.Call.__name__, set())
    tcss_mappings = _tcss_mapping_names(node_db)

    for node_data in call_nodes:
        assert isinstance(node_data.ast_node, ast.Call)
        call = node_data.ast_node

        # 1. Check keyword arguments: Widget(..., classes="hardcoded")
        for kw in call.keywords:
            if kw.arg == "classes":
                _validate_tcss_expr(
                    kw.value,
                    node_data.rel_path,
                    node_data.lineno,
                    issues,
                    tcss_mappings,
                )

        # 2. Check method calls: widget.add_class("hardcoded")
        if (
            isinstance(call.func, ast.Attribute)
            and call.func.attr == "add_class"
            and call.args
        ):
            _validate_tcss_expr(
                call.args[0],
                node_data.rel_path,
                node_data.lineno,
                issues,
                tcss_mappings,
            )

    return issues


def _terminal_name(expr: ast.expr) -> str | None:
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        return expr.attr
    return None


def _tcss_mapping_names(node_db: NodeDb) -> set[str]:
    """Names of variables annotated as dict[<key>, Tcss]."""
    names: set[str] = set()
    for data in node_db.by_type.get(ast.AnnAssign.__name__, set()):
        node = data.ast_node
        if not isinstance(node, ast.AnnAssign):
            continue
        ann = ast.unparse(node.annotation)
        if re.search(r"dict\[[^\]]*,\s*Tcss\]", ann):
            name = _terminal_name(node.target)
            if name:
                names.add(name)
    return names


def _validate_tcss_expr(
    expr: ast.expr,
    rel_path: str,
    lineno: int | None,
    issues: list[tuple[str, str, str]],
    tcss_mappings: set[str],
) -> None:
    loc = f"{rel_path}:{lineno or 0}"
    # Allow `<mapping>[key].value` where the mapping is annotated dict[..., Tcss]
    if (
        isinstance(expr, ast.Attribute)
        and expr.attr == "value"
        and isinstance(expr.value, ast.Subscript)
        and _terminal_name(expr.value.value) in tcss_mappings
    ):
        return

    # Flag string literals directly: classes="flat_button"
    if (
        isinstance(expr, ast.Constant)
        and isinstance(expr.value, str)
        and expr.value not in EXCLUDE_TCSS_CLASSES
    ):
        issues.append(
            (
                ast.unparse(expr),
                loc,
                "Hardcoded string literal used instead of Tcss enum",
            )
        )


def get_tcss_issues(node_db: NodeDb) -> list[tuple[str, str, str]]:
    issues: list[tuple[str, str, str]] = []
    issues.extend(check_tcss_classes_in_enum())
    issues.extend(check_tcss_type_selectors(node_db))
    issues.extend(check_hardcoded_tcss_strings(node_db))
    return issues


def test_tcss() -> None:

    # Gather data from the external gui.tcss file

    # Create a Tcss enum member set
    tcss_enum_members = {member.value for member in Tcss}

    errors: list[str] = []

    # Check orphaned TCSS classes (Not in Tcss StrEnum)
    orphaned_classes: list[str] = []
    for tcss_class in gui_tcss.class_selectors:
        stripped = tcss_class.lstrip(".")
        if stripped in EXCLUDE_TCSS_CLASSES:
            continue
        if stripped not in tcss_enum_members:
            orphaned_classes.append(tcss_class)

    if orphaned_classes:
        errors.append(
            "\nTCSS classes not defined in Tcss Enum:\n" + ", ".join(orphaned_classes)
        )

    # Check orphaned TCSS type selectors

    if errors:
        pytest.fail("\n".join(errors))
