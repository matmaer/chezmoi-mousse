"""Test to ensure CSS classes are properly managed through TcssStr enum."""

import ast
import re
from pathlib import Path

import pytest
from _test_utils import get_strenum_member_names, modules_to_test

from chezmoi_mousse.constants import TcssStr

classes_kw = "classes"
add_class_method = "add_class"
exclude_files = ["id_typing.py", "__init__.py", "__main__.py", "constants.py"]


def extract_tcss_classes(path: Path) -> list[str]:
    pattern = r"[.][^a-z]*([a-z][a-z_]*(?=.*_)[a-z_]*)(?=\s|,|$)"
    with open(path, "r") as f:
        content = f.read()
        matches = re.findall(pattern, content, re.MULTILINE)
    return matches


def get_used_tcss_members() -> set[str]:
    """Get all TcssStr enum members that are used in Python code."""
    used_members: set[str] = set()

    for py_file in modules_to_test(exclude_file_names=exclude_files):
        tree = ast.parse(py_file.read_text())

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                # Check for TcssStr.member_name patterns
                if (
                    isinstance(node.value, ast.Name)
                    and node.value.id == "TcssStr"
                    and hasattr(TcssStr, node.attr)
                ):
                    used_members.add(node.attr)

    return used_members


@pytest.mark.parametrize(
    "py_file",
    modules_to_test(exclude_file_names=exclude_files),
    ids=lambda py_file: py_file.name,
)
def test_no_hardcoded(py_file: Path) -> None:
    tree = ast.parse(py_file.read_text())

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):  # skip anything but function calls
            continue

        for keyword in node.keywords:
            if keyword.arg == classes_kw:  # classes= keyword is used
                if not (
                    isinstance(keyword.value, ast.Attribute)
                    and hasattr(TcssStr, keyword.value.attr)
                ):
                    pytest.fail(
                        f"\n{py_file} line {keyword.lineno}: {keyword.value}: hardcoded tcss class"
                    )

        # Check add_class method calls for string literals
        if (
            isinstance(node.func, ast.Attribute)  # some_object.add_class()
            and node.func.attr == add_class_method
            and len(node.args) >= 1
        ):
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Constant) and isinstance(
                first_arg.value, str
            ):
                pytest.fail(
                    f'\n{py_file}:{first_arg.lineno} - add_class("{first_arg.value}"): hardcoded tcss class'
                )


@pytest.mark.parametrize(
    "tcss_class", extract_tcss_classes(Path("./src/chezmoi_mousse/gui.tcss"))
)
def test_no_orphaned_tcss_classes(tcss_class: str) -> None:
    """Test that each CSS class in gui.tcss is also defined as a TcssStr enum member."""
    tcss_enum_members = {member.name for member in TcssStr}

    if tcss_class not in tcss_enum_members:
        pytest.fail(
            f"\nOrphaned CSS class '{tcss_class}' found in gui.tcss (not in TcssStr enum)"
        )


@pytest.mark.parametrize(
    "tcss_member",
    get_strenum_member_names(TcssStr),
    ids=lambda tcss_member: tcss_member.attr,
)
def test_no_orphaned_tcss_members(tcss_member: ast.Attribute) -> None:
    """Test that each TcssStr enum member has a corresponding class in gui.tcss."""
    tcss_classes = extract_tcss_classes(Path("./src/chezmoi_mousse/gui.tcss"))

    if tcss_member.attr not in tcss_classes:
        pytest.fail(
            f"\nOrphaned TcssStr member '{tcss_member.attr}' found (no corresponding CSS class in gui.tcss)"
        )
