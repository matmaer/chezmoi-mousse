"""Test to ensure CSS classes are properly managed through Tcss enum."""

import ast
import re
from pathlib import Path

import pytest
from _test_utils import get_module_paths, get_strenum_member_names

from chezmoi_mousse.id_typing import Tcss

add_class_method = "add_class"
classes_kw = "classes"
exclude_files = ["id_typing.py", "_str_enums.py"]
tcss_path = Path("./src/chezmoi_mousse/data/gui.tcss")


def extract_tcss_classes(path: Path) -> list[str]:
    pattern = r"[.][^a-z]*([a-z][a-z_]*(?=.*_)[a-z_]*)(?=\s|,|$)"
    with open(path, "r") as f:
        content = f.read()
        matches = re.findall(pattern, content, re.MULTILINE)
    return matches


def get_used_tcss_members() -> set[str]:
    """Get all Tcss enum members that are used in Python code."""
    used_members: set[str] = set()

    for py_file in get_module_paths(exclude_file_names=exclude_files):
        tree = ast.parse(py_file.read_text())

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                # Check for Tcss.member_name patterns
                if (
                    isinstance(node.value, ast.Name)
                    and node.value.id == "Tcss"
                    and hasattr(Tcss, node.attr)
                ):
                    used_members.add(node.attr)

    return used_members


@pytest.mark.parametrize(
    "py_file",
    get_module_paths(exclude_file_names=exclude_files),
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
                    and hasattr(Tcss, keyword.value.attr)
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


@pytest.mark.parametrize("tcss_class", extract_tcss_classes(tcss_path))
def test_no_orphaned_gui_tcss_classes(tcss_class: str) -> None:
    """Test that each CSS class in gui.tcss is also defined as a Tcss enum member."""
    tcss_enum_members = {member.name for member in Tcss}

    if tcss_class not in tcss_enum_members:
        pytest.fail(
            f"\nOrphaned CSS class '{tcss_class}' found in gui.tcss (not in Tcss enum)"
        )


@pytest.mark.parametrize(
    "tcss_member",
    get_strenum_member_names(Tcss),
    ids=lambda tcss_member: tcss_member.attr,
)
def test_no_orphaned_tcss_str_members(tcss_member: ast.Attribute) -> None:
    """Test that each Tcss enum member has a corresponding class in gui.tcss."""
    tcss_classes = extract_tcss_classes(tcss_path)

    if tcss_member.attr not in tcss_classes:
        pytest.fail(
            f"\nOrphaned Tcss member '{tcss_member.attr}' found (no corresponding CSS class in gui.tcss)"
        )
