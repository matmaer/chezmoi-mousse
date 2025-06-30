"""Test to ensure CSS classes are properly managed through TcssStr enum."""

import ast
import re
from pathlib import Path

import pytest

from _test_utils import tcss_file_path, get_modules_to_test


@pytest.mark.parametrize(
    "py_file", get_modules_to_test(), ids=lambda x: x.name
)
def test_no_hardcoded_css_classes(py_file: Path) -> None:
    """Verify that classes= parameters don't use hardcoded string literals."""

    content = py_file.read_text()
    violations: list[str] = []

    # Parse the AST to find function calls with classes= keyword arguments
    tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg == "classes":
                    # Check if the value is a string literal
                    if isinstance(keyword.value, ast.Constant) and isinstance(
                        keyword.value.value, str
                    ):
                        # Found a hardcoded string in classes=
                        line_num = keyword.value.lineno
                        violations.append(
                            f'{py_file}:{line_num} - classes="{keyword.value.value}"'
                        )

    assert (
        not violations
    ), "Found hardcoded CSS classes in classes= parameters:\n" + "\n".join(
        violations
    )


def test_tcss_str_enum_proper_usage() -> None:
    """Verify that TcssStr entries are used correctly in the codebase."""
    tcss_str_usage_count = 0
    hardcoded_violations: list[str] = []
    python_files = get_modules_to_test()

    for py_file in python_files:
        content = py_file.read_text()

        # Count occurrences of TcssStr usage
        tcss_str_usage_count += content.count("TcssStr.")

        # Parse the AST to find function calls with classes= and id= keyword arguments
        try:
            tree = ast.parse(content)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if keyword.arg == "classes":
                        # Check if the value is a string literal (ast.Constant with str value)
                        if isinstance(
                            keyword.value, ast.Constant
                        ) and isinstance(keyword.value.value, str):
                            # Found a hardcoded string in classes=
                            line_num = keyword.value.lineno
                            hardcoded_violations.append(
                                f'{py_file.name}:{line_num} - classes="{keyword.value.value}"'
                            )

    # Check for hardcoded CSS classes in classes= parameters
    assert (
        not hardcoded_violations
    ), "Found hardcoded CSS classes in classes= parameters:\n" + "\n".join(
        hardcoded_violations
    )


def test_no_unused_tcss_classes() -> None:

    tcss_content = tcss_file_path.read_text()

    # Extract CSS class names (starting with .)
    css_class_pattern = re.compile(r"\.([a-zA-Z_][a-zA-Z0-9_-]*)")
    defined_classes = set(css_class_pattern.findall(tcss_content))
    used_classes: set[str] = set()
    python_files = get_modules_to_test()

    # Search for class usage in Python files
    for py_file in python_files:
        content = py_file.read_text()

        # Look for classes in TcssStr enum values
        tcss_enum_pattern = re.compile(r"TcssStr\.([a-zA-Z_][a-zA-Z0-9_]*)")
        enum_matches = tcss_enum_pattern.findall(content)
        used_classes.update(enum_matches)

        # Also look for direct string usage (fallback)
        for css_class in defined_classes:
            # Convert snake_case to kebab-case for searching
            kebab_class = css_class.replace("_", "-")
            if kebab_class in content or css_class in content:
                used_classes.add(css_class)

    # Find unused classes
    unused_classes = defined_classes - used_classes

    # Filter out classes that are automatically applied by Textual widgets
    # These are CSS classes that Textual applies internally to widgets
    textual_internal_classes = {
        # Pseudo-state classes
        "visible",
        "on",
        "hover",
        "focus",
        "disabled",
        "last-clicked",
        # DataTable internal classes
        "datatable--header",
        # DirectoryTree internal classes
        "directory-tree--extension",
        "directory-tree--file",
        "directory-tree--folder",
        "directory-tree--hidden",
        # Tree internal classes
        "tree--guides",
        "tree--guides-hover",
        "tree--guides-selected",
        "tree--highlight",
        "tree--highlight-line",
        # Switch internal classes
        "switch--slider",
        # CheckBox internal classes
        "toggle--button",
        # Custom dynamic classes (applied via code logic)
        "operate-buttons-horizontal",
        "operate-diff-view",
        "modal-view",
    }

    unused_classes = {
        cls for cls in unused_classes if cls not in textual_internal_classes
    }

    assert not unused_classes, (
        "Found unused CSS classes in gui.tcss:\n"
        + "\n".join(sorted(f"  .{cls}" for cls in unused_classes))
        + "\nConsider removing these unused classes or verify they are actually needed."
    )


if __name__ == "__main__":
    test_tcss_str_enum_proper_usage()
    test_no_unused_tcss_classes()
