"""Test to ensure CSS classes are properly managed through TcssStr enum."""

import ast
import re
from pathlib import Path

import pytest
from _test_utils import modules_to_test

from chezmoi_mousse.id_typing import TcssStr

classes_kw = "classes"
add_class_method = "add_class"
exclude_files = ["id_typing.py", "__init__.py", "__main__.py"]


def extract_tcss_classes(path: Path) -> list[str]:
    pattern = r"(?:^|\s)[.&][^a-z]*([a-z][a-z_]*(?=.*_)[a-z_]*)(?=\s|,|$)"
    with open(path, "r") as f:
        content = f.read()
        matches = re.findall(pattern, content, re.MULTILINE)
    return matches


def get_used_tcss_members() -> set[str]:
    """Get all TcssStr enum members that are used in Python code."""
    used_members: set[str] = set()

    for py_file in modules_to_test(exclude_file_names=exclude_files):
        content = py_file.read_text()
        # Find TcssStr.member_name patterns
        for member in TcssStr:
            if f"TcssStr.{member.name}" in content:
                used_members.add(member.name)

    return used_members


@pytest.mark.parametrize("tcss_member", [member.name for member in TcssStr])
def test_tcss_member_in_use(tcss_member: str) -> None:
    """Test that each TcssStr member is both defined in gui.tcss AND used in Python code."""
    tcss_classes = extract_tcss_classes(Path("./src/chezmoi_mousse/gui.tcss"))
    used_members = get_used_tcss_members()

    is_in_tcss = tcss_member in tcss_classes
    is_used_in_python = tcss_member in used_members

    if not is_in_tcss and not is_used_in_python:
        pytest.fail(
            f"TcssStr.{tcss_member} is neither in gui.tcss nor used in Python code"
        )
    elif not is_in_tcss:
        pytest.fail(
            f"TcssStr.{tcss_member} is used in Python but not defined in gui.tcss"
        )
    elif not is_used_in_python:
        pytest.fail(
            f"TcssStr.{tcss_member} is defined in gui.tcss but not used in Python code"
        )


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
                        f"{py_file} line {keyword.lineno}: {keyword.value}"
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
                    f'{py_file}:{first_arg.lineno} - add_class("{first_arg.value}")'
                )
