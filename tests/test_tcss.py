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

    pattern = r"(?:^|\s)[.&][^a-z]*([a-z][a-z_]*(?=.*_)[a-z_]*)(?=\s|$)"
    with open(path, "r") as f:
        content = f.read()
        matches = re.findall(pattern, content, re.MULTILINE)
    return matches


@pytest.mark.parametrize(
    "tcss_class", extract_tcss_classes(Path("./src/chezmoi_mousse/gui.tcss"))
)
def test_no_unused(tcss_class: str) -> None:
    is_used = False
    for py_file in modules_to_test(exclude_file_names=exclude_files):
        if tcss_class in py_file.read_text():
            is_used = True
            break  # Found it, no need to check other files

    if not is_used:
        pytest.fail(f"unused tcss class: {tcss_class}")


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
