import ast
import re
from pathlib import Path

import pytest
from _test_utils import MODULE_DIR, ast_parse, get_file_paths

from chezmoi_mousse import Tcss

with Path.open(Path("src", "chezmoi_mousse", "gui.tcss")) as f:
    tcss_lines = [
        line for line in f.read().splitlines() if not line.startswith(("/", "#"))
    ]
    tcss_content = "\n".join(tcss_lines)

EXCLUDE_TCSS_CLASSES = ["-visible"]

EXCLUDE_TYPE_SELECTORS = {
    # TODO: don't use type selectors if the classes are not present our code
    # in that case, find another selector solution
    "CheckBox",
    "CollapsibleTitle",
    "Contents",
    "SelectCurrent",
    "SelectOverlay",
    "Tab",
    "Toast",
}


def extract_tcss_classes() -> list[str]:
    pattern = r"\.[^a-z]*[a-z][a-z_]*(?=.*_)[a-z_]*(?=\s|,|$)"
    return re.findall(pattern, tcss_content)


def extract_type_selectors() -> set[str]:
    pattern = r"\b(?=[A-Z][A-Za-z]*[a-z])[A-Z][A-Za-z]*\b"
    matches: set[str] = set()
    for line in tcss_lines:
        matches.update(re.findall(pattern, line))
    return matches


def imports_from_textual(tree: ast.AST) -> bool:
    return any(
        (
            isinstance(node, ast.Import)
            and any(
                alias.name == "textual" or alias.name.startswith("textual.")
                for alias in node.names
            )
        )
        or (
            isinstance(node, ast.ImportFrom)
            and (
                node.module == "textual"
                or (node.module and node.module.startswith("textual."))
            )
        )
        for node in ast.walk(tree)
    )


class TcssHousekeepingVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.current_file: str = ""
        self.is_gui_file: bool = False
        self.imports_tcss: bool = False

        # Only track definitions/imports that happen inside GUI/debug/app files
        self.gui_eligible_classes: set[str] = set()

        # Tracking for hardcoded tcss string violations: "file:line" -> code_str
        self.hardcoded_violations: dict[str, str] = {}

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        # Track if this file is actively using the Tcss enum
        if (
            node.module == "chezmoi_mousse"
            or node.level > 0
            and any(alias.name == "Tcss" for alias in node.names)
        ):
            self.imports_tcss = True

        # Gather CamelCase imports to find orphaned type-selectors in the tcss file
        if self.is_gui_file:
            for alias in node.names:
                if alias.name.casefold() != alias.name:
                    self.gui_eligible_classes.add(alias.name)

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if self.is_gui_file:
            self.gui_eligible_classes.add(node.name)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if self.imports_tcss:
            # Check for: classes="hardcoded-string" keyword arguments
            for keyword in node.keywords:
                if keyword.arg == "classes":
                    self._check_expression_for_hardcoded(keyword.value)

            # Check for: some_object.add_class("hardcoded-string")
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_class"
                and node.args
            ):
                self._check_expression_for_hardcoded(node.args[0])

        self.generic_visit(node)

    def _check_expression_for_hardcoded(self, expr: ast.expr) -> None:
        if not isinstance(expr, ast.Attribute):
            if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
                if expr.value not in EXCLUDE_TCSS_CLASSES:
                    loc = f"{self.current_file}:{expr.lineno}"
                    self.hardcoded_violations[loc] = ast.unparse(expr)
            else:
                # Catch complex dynamic expressions or f-strings that aren't safe
                # Attribute lookups
                loc = f"{self.current_file}:{expr.lineno}"
                self.hardcoded_violations[loc] = ast.unparse(expr)


def test_tcss() -> None:

    visitor = TcssHousekeepingVisitor()

    for file_path in get_file_paths():
        visitor.current_file = str(file_path.relative_to(MODULE_DIR))
        # Reset file-specific flags context before walking
        visitor.imports_tcss = False

        # Prepare new visit
        tree = ast_parse(file_path)
        # A file is a GUI file if it imports 'textual' or from 'textual.*'
        visitor.is_gui_file = imports_from_textual(tree)
        visitor.visit(tree)

    # Gather data from the external gui.tcss file
    type_selectors = extract_type_selectors()

    # Create a Tcss enum member set
    tcss_enum_members = {member.value for member in Tcss}

    errors: list[str] = []

    # Check orphaned TCSS classes (Not in Tcss StrEnum)
    orphaned_classes: list[str] = []
    for tcss_class in extract_tcss_classes():
        stripped = tcss_class.lstrip(".")
        if stripped in EXCLUDE_TCSS_CLASSES:
            continue
        if stripped not in tcss_enum_members:
            orphaned_classes.append(tcss_class)

    if orphaned_classes:
        errors.append(
            "\nTCSS classes not defined in Tcss Enum:\n" + ", ".join(orphaned_classes)
        )

    # Check hardcoded TCSS usage violations
    if visitor.hardcoded_violations:
        violations_report = [
            f"- {loc} has hardcoded tcss class: {code}"
            for loc, code in visitor.hardcoded_violations.items()
        ]
        errors.append(
            "\nHardcoded TCSS assignments detected:\n" + ", ".join(violations_report)
        )

    # Check orphaned TCSS type selectors
    orphaned_selectors = (
        type_selectors - visitor.gui_eligible_classes - EXCLUDE_TYPE_SELECTORS
    )
    if orphaned_selectors:
        errors.append(
            "\nTCSS Type selectors not matching any Python Class:\n"
            + ", ".join(orphaned_selectors)
        )

    if errors:
        pytest.fail("\n".join(errors))
