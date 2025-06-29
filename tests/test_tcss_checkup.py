"""Test to ensure CSS classes are properly managed through TcssStr enum."""

import ast
import re
from pathlib import Path

from test_utils import get_python_files


def test_no_hardcoded_css_classes_in_code():
    """Verify that classes= parameters don't use hardcoded string literals."""
    python_files = get_python_files()
    violations: list[str] = []

    for py_file in python_files:

        content = py_file.read_text()

        # Parse the AST to find function calls with classes= keyword arguments
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
                            violations.append(
                                f'{py_file.name}:{line_num} - classes="{keyword.value.value}"'
                            )

    assert (
        not violations
    ), "Found hardcoded CSS classes in classes= parameters:\n" + "\n".join(
        violations
    )


def test_no_hardcoded_css_classes_regex_fallback():
    """Regex-based fallback test to catch any missed hardcoded CSS classes.

    This test uses regex to find patterns like classes="..." as a secondary check.
    """
    python_files = get_python_files()
    # Pattern to match classes="..." or classes='...'
    pattern = re.compile(r'classes\s*=\s*["\'][^"\']*["\']')
    violations: list[str] = []

    for py_file in python_files:

        content = py_file.read_text()
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            matches = pattern.findall(line)
            for match in matches:
                violations.append(f"{py_file.name}:{line_num} - {match}")

    assert (
        not violations
    ), "Found hardcoded CSS classes using regex check:\n" + "\n".join(
        violations
    )


def test_tcss_str_enum_usage():
    """Verify that TcssStr enum values are being used for CSS classes.

    This test checks that the codebase is actually using the TcssStr enum
    for CSS class management.
    """
    python_files = get_python_files()
    tcss_str_usage_count = 0

    for py_file in python_files:

        content = py_file.read_text()

        # Count occurrences of TcssStr usage
        tcss_str_usage_count += content.count("TcssStr.")

    # We expect significant usage of TcssStr in the codebase
    assert (
        tcss_str_usage_count > 20
    ), f"Expected significant TcssStr usage, found only {tcss_str_usage_count} occurrences"


def test_no_unused_tcss_classes():
    """Verify that all CSS classes defined in gui.tcss are actually used in the codebase.

    This test prevents accumulation of unused CSS classes in the stylesheet.
    """
    # Read the CSS file
    tcss_file = (
        Path(__file__).parent.parent / "src" / "chezmoi_mousse" / "gui.tcss"
    )
    tcss_content = tcss_file.read_text()

    # Extract CSS class names (starting with .)
    css_class_pattern = re.compile(r"\.([a-zA-Z_][a-zA-Z0-9_-]*)")
    defined_classes = set(css_class_pattern.findall(tcss_content))

    # Get all Python files
    python_files = get_python_files()
    used_classes: set[str] = set()

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
    test_no_hardcoded_css_classes_in_code()
    test_no_hardcoded_css_classes_regex_fallback()
    test_tcss_str_enum_usage()
    test_no_unused_tcss_classes()
    print("All CSS class management tests passed!")
