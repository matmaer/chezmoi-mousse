"""Test to ensure CSS classes are properly managed through TcssStr enum."""

import ast
import re
from pathlib import Path

import pytest

from _test_utils import tcss_file_path, get_modules_to_test


def _is_tcssstr_attribute(node: ast.Attribute) -> bool:
    return isinstance(node.value, ast.Name) and node.value.id == "TcssStr"


@pytest.mark.parametrize(
    "py_file", get_modules_to_test(), ids=lambda x: x.name
)
def test_no_hardcoded_css_classes(py_file: Path) -> None:
    content = py_file.read_text()
    violations: list[str] = []
    tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check classes= keyword arguments for string literals
            for keyword in node.keywords:
                if (
                    keyword.arg == "classes"
                    and isinstance(keyword.value, ast.Constant)
                    and isinstance(keyword.value.value, str)
                ):
                    violations.append(
                        f'{py_file}:{keyword.value.lineno} - classes="{keyword.value.value}"'
                    )

            # Check add_class method calls for string literals
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_class"
                and len(node.args) >= 1
            ):
                first_arg = node.args[0]
                if isinstance(first_arg, ast.Constant) and isinstance(
                    first_arg.value, str
                ):
                    violations.append(
                        f'{py_file}:{first_arg.lineno} - add_class("{first_arg.value}")'
                    )

    assert not violations, "Found hardcoded CSS classes:\n" + "\n".join(
        violations
    )


@pytest.mark.parametrize(
    "py_file", get_modules_to_test(), ids=lambda x: x.name
)
def test_only_tcssstr_attributes(py_file: Path) -> None:
    content = py_file.read_text()
    violations: list[str] = []
    tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check classes= keyword arguments for non-TcssStr attributes
            for keyword in node.keywords:
                if (
                    keyword.arg == "classes"
                    and isinstance(keyword.value, ast.Attribute)
                    and not _is_tcssstr_attribute(keyword.value)
                ):
                    violations.append(
                        f"{py_file}:{keyword.value.lineno} - classes= uses non-TcssStr attribute"
                    )

            # Check add_class method calls for non-TcssStr attributes
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_class"
                and len(node.args) >= 1
            ):
                first_arg = node.args[0]
                if isinstance(
                    first_arg, ast.Attribute
                ) and not _is_tcssstr_attribute(first_arg):
                    violations.append(
                        f"{py_file}:{first_arg.lineno} - add_class() uses non-TcssStr attribute"
                    )

    assert (
        not violations
    ), "Found non-TcssStr attributes in CSS class assignments:\n" + "\n".join(
        violations
    )


def test_no_unused_tcss_classes() -> None:
    # Test if defined TCSS classes in gui.tcss are all in use."""
    tcss_content = tcss_file_path.read_text()

    # Extract CSS class names (lowercase with underscores)
    css_class_pattern = re.compile(r"\.([a-z]+_[a-z_]*)\b")
    defined_classes = set(css_class_pattern.findall(tcss_content))

    used_classes: set[str] = set()

    for py_file in get_modules_to_test():
        content = py_file.read_text()
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check classes= keyword arguments
                for keyword in node.keywords:
                    if keyword.arg == "classes":
                        # Direct TcssStr.class_name attribute access
                        if (
                            isinstance(keyword.value, ast.Attribute)
                            and _is_tcssstr_attribute(keyword.value)
                            and keyword.value.attr in defined_classes
                        ):
                            used_classes.add(keyword.value.attr)

                        # f-string with TcssStr attributes
                        elif isinstance(keyword.value, ast.JoinedStr):
                            for value in keyword.value.values:
                                if (
                                    isinstance(value, ast.FormattedValue)
                                    and isinstance(value.value, ast.Attribute)
                                    and _is_tcssstr_attribute(value.value)
                                    and value.value.attr in defined_classes
                                ):
                                    used_classes.add(value.value.attr)

                # Check add_class method calls
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "add_class"
                    and len(node.args) >= 1
                ):
                    first_arg = node.args[0]
                    if (
                        isinstance(first_arg, ast.Attribute)
                        and _is_tcssstr_attribute(first_arg)
                        and first_arg.attr in defined_classes
                    ):
                        used_classes.add(first_arg.attr)

    unused_classes = defined_classes - used_classes
    assert (
        not unused_classes
    ), f"Found {len(unused_classes)} unused CSS classes: {sorted(unused_classes)}"
