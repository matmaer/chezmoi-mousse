import ast
import re
from pathlib import Path

import pytest
from _test_utils import get_modules_importing_class

from chezmoi_mousse._str_enum_names import Tcss

CLASS_NAME = "Tcss"
CLASSES_KEYWORD = "classes"
GUI_DOT_TCSS_PATH = Path("src", "chezmoi_mousse", "gui", "gui.tcss")
HARDCODED = "hardcoded tcss class"
ORPHANED = "Orphaned gui.tcss classes"


def extract_tcss_classes() -> list[str]:
    pattern = r"\.[^a-z]*[a-z][a-z_]*(?=.*_)[a-z_]*(?=\s|,|$)"
    with open(GUI_DOT_TCSS_PATH, "r") as f:
        content = f.read()
        matches = re.findall(pattern, content)
    return matches


def test_not_in_use() -> None:
    result: list[str] = []
    tcss_classes = extract_tcss_classes()
    tcss_enum_members = [member.value for member in Tcss]

    for tcss_class in tcss_classes:
        # allow matching either the bare member value or the dot-prefixed form
        if tcss_class.lstrip(".") not in tcss_enum_members:
            result.append(tcss_class)

    if len(result) > 0:
        pytest.fail(f"\nTcss classes not in Tcss enum:\n{'\n'.join(result)}")


@pytest.mark.parametrize(
    "py_file",
    get_modules_importing_class(class_name=CLASS_NAME),
    ids=lambda py_file: py_file.name,
)
def test_no_hardcoded(py_file: Path) -> None:
    results: list[str] = []
    tree = ast.parse(py_file.read_text())

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            # tcss classes are always set in ast.Call nodes
            continue

        for keyword in node.keywords:
            if keyword.arg == CLASSES_KEYWORD:  # classes= keyword is used
                if not (isinstance(keyword.value, ast.Attribute)):
                    results.append(
                        f"\n{py_file} line {keyword.lineno}: {keyword.value}: {HARDCODED}"
                    )

    if len(results) > 0:
        pytest.fail("".join(results))
