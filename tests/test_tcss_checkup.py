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


def test_no_unused_tcss_classes() -> None:
    tcss_content = tcss_file_path.read_text()

    # Extract CSS class names (starting with .) - only lowercase and underscore-based classes
    css_class_pattern = re.compile(r"\.([a-z]+_[a-z_]*)\b")
    defined_classes = set(css_class_pattern.findall(tcss_content))

    # Find all used classes across all Python modules
    used_classes: set[str] = set()

    for py_file in get_modules_to_test():
        content = py_file.read_text()
        tree = ast.parse(content)

        # Parse the AST to find TcssStr.class_name usage in classes= arguments
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if keyword.arg == "classes":
                        # Check for TcssStr.class_name attribute access
                        if isinstance(keyword.value, ast.Attribute):
                            if (
                                isinstance(keyword.value.value, ast.Name)
                                and keyword.value.value.id == "TcssStr"
                                and keyword.value.attr in defined_classes
                            ):
                                used_classes.add(keyword.value.attr)

                        # Check for f-strings that might contain TcssStr.class_name
                        elif isinstance(keyword.value, ast.JoinedStr):
                            for value in keyword.value.values:
                                if isinstance(value, ast.FormattedValue):
                                    if isinstance(value.value, ast.Attribute):
                                        if (
                                            isinstance(
                                                value.value.value, ast.Name
                                            )
                                            and value.value.value.id
                                            == "TcssStr"
                                            and value.value.attr
                                            in defined_classes
                                        ):
                                            used_classes.add(value.value.attr)

    unused_classes = defined_classes - used_classes

    assert (
        not unused_classes
    ), f"Found {len(unused_classes)} unused CSS classes: {sorted(unused_classes)}"
