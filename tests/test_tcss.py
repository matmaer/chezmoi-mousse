"""Test to ensure CSS classes are properly managed through Tcss enum."""

import ast
import re
from pathlib import Path

import pytest
from _test_utils import get_modules_importing_class

from chezmoi_mousse.id_typing.enums import Tcss

add_class_method = "add_class"
classes_kw = "classes"
tcss_path = Path("./src/chezmoi_mousse/data/gui.tcss")


def extract_tcss_classes(path: Path) -> list[str]:
    pattern = r"[.][^a-z]*([a-z][a-z_]*(?=.*_)[a-z_]*)(?=\s|,|$)"
    with open(path, "r") as f:
        content = f.read()
        matches = re.findall(pattern, content, re.MULTILINE)
    return matches


def test_no_orphaned() -> None:
    tcss_classes = set(extract_tcss_classes(tcss_path))
    tcss_enum_members = {member.name for member in Tcss}

    orphaned_classes = tcss_classes - tcss_enum_members
    orphaned_members = tcss_enum_members - tcss_classes

    result = ""
    if orphaned_classes:
        orphaned_list = "\n".join(
            f"- {cls}" for cls in sorted(orphaned_classes)
        )
        result += f"\nOrphaned gui.tcss classes (not found in Tcss):\n{orphaned_list}\n"

    if orphaned_members:
        orphaned_list = "\n".join(
            f"- {mem}" for mem in sorted(orphaned_members)
        )
        result += f"\nOrphaned Tcss members (not found in gui.tcss):\n{orphaned_list}\n"

    # make sure we only make one pytest.fail call
    if result:
        pytest.fail(f"\n{result}")


@pytest.mark.parametrize(
    "py_file",
    get_modules_importing_class(class_name="Tcss"),
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
