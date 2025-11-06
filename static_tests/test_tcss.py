import ast
import re
from pathlib import Path

import pytest
from _test_utils import get_modules_importing_class

from chezmoi_mousse._tcss_classes import Tcss

ADD_CLASS_METHOD = "add_class"
CLASS_NAME = "Tcss"
CLASSES_KEYWORD = "classes"
GUI_DOT_TCSS_PATH = Path("src", "chezmoi_mousse", "gui", "_gui.tcss")
HARDCODED = "hardcoded tcss class"
ORPHANED = "Orphaned gui.tcss classes"


def extract_tcss_classes() -> list[str]:
    pattern = r"\.[^a-z]*[a-z][a-z_]*(?=.*_)[a-z_]*(?=\s|,|$)"
    with open(GUI_DOT_TCSS_PATH, "r") as f:
        content = f.read()
        matches = re.findall(pattern, content)
    return matches


def test_tcss_class_not_in_tcss_enum() -> None:
    result: list[str] = []
    tcss_classes = extract_tcss_classes()
    tcss_enum_members = [member.value for member in Tcss]

    for tcss_class in tcss_classes:
        if tcss_class not in tcss_enum_members:
            result.append(tcss_class)

    if len(result) > 0:
        pytest.fail(f"\nTcss classes not in Tcss enum:\n{'\n'.join(result)}")


def get_attr_chain(node: ast.AST) -> list[str] | None:
    attrs: list[str] = []
    cur = node
    while isinstance(cur, ast.Attribute):
        attrs.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        attrs.append(cur.id)
        attrs.reverse()
        return attrs
    return None


def is_allowed_enum_attr(node: ast.AST) -> bool:
    chain = get_attr_chain(node)
    if not chain:
        return False
    # require at least Enum.member and that the member exists on Tcss
    if len(chain) >= 2:
        member = chain[1]
        return hasattr(Tcss, member)
    return False


@pytest.mark.parametrize(
    "py_file",
    get_modules_importing_class(class_name=CLASS_NAME),
    ids=lambda py_file: py_file.name,
)
def test_no_hardcoded(py_file: Path) -> None:
    tree = ast.parse(py_file.read_text())

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):  # skip anything but function calls
            continue

        for keyword in node.keywords:
            if keyword.arg == CLASSES_KEYWORD:  # classes= keyword is used
                if not (
                    isinstance(keyword.value, ast.Attribute)
                    and is_allowed_enum_attr(keyword.value)
                ):
                    pytest.fail(
                        f"\n{py_file} line {keyword.lineno}: {keyword.value}: {HARDCODED}"
                    )

        # Check add_class method calls for string literals
        if (
            isinstance(node.func, ast.Attribute)  # some_object.add_class()
            and node.func.attr == ADD_CLASS_METHOD
            and len(node.args) >= 1
        ):
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Constant) and isinstance(
                first_arg.value, str
            ):
                pytest.fail(
                    f'\n{py_file}:{first_arg.lineno} - add_class("{first_arg.value}"): {HARDCODED}'
                )
            if isinstance(
                first_arg, ast.Attribute
            ) and not is_allowed_enum_attr(first_arg):
                pytest.fail(
                    f"\n{py_file}:{first_arg.lineno} - add_class({ast.unparse(first_arg)}): {HARDCODED}"
                )
