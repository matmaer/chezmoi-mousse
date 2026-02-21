import ast
import re
from pathlib import Path
from typing import NamedTuple

import pytest
from _test_utils import get_module_ast_tree, get_modules_importing_class

from chezmoi_mousse import Tcss

CLASS_NAME = "Tcss"
CLASSES_KEYWORD = "classes"
GUI_DOT_TCSS_PATH = Path("src", "chezmoi_mousse", "gui", "gui.tcss")
HARDCODED = "hardcoded tcss class"

EXCLUDE_TCSS_CLASSES = ["-visible"]


class HardcodedTcssData(NamedTuple):
    module_path: str
    line_number: int
    code: str


def extract_tcss_classes() -> list[str]:
    pattern = r"\.[^a-z]*[a-z][a-z_]*(?=.*_)[a-z_]*(?=\s|,|$)"
    with open(GUI_DOT_TCSS_PATH, "r") as f:
        content = f.read()
        matches = re.findall(pattern, content)
    return matches


def test_not_in_use() -> None:
    tcss_classes = extract_tcss_classes()
    tcss_enum_members = [member.value for member in Tcss]

    orphaned: list[str] = []
    for tcss_class in tcss_classes:
        # allow matching either the bare member value or the dot-prefixed form
        stripped_class = tcss_class.lstrip(".")
        # Skip excluded classes
        if stripped_class in EXCLUDE_TCSS_CLASSES:
            continue
        if stripped_class not in tcss_enum_members:
            orphaned.append(tcss_class)

    if orphaned:
        pytest.fail(f"Tcss classes not in Tcss enum:\n{chr(10).join(orphaned)}")


def _check_file_for_hardcoded(py_file: Path) -> list[HardcodedTcssData]:
    hardcoded_results: list[HardcodedTcssData] = []
    for node in ast.walk(get_module_ast_tree(py_file)):
        if not isinstance(node, ast.Call):
            # tcss classes are always set in ast.Call nodes
            continue

        for keyword in node.keywords:
            if keyword.arg == CLASSES_KEYWORD:  # classes= keyword is used
                if not (isinstance(keyword.value, ast.Attribute)):
                    code_str = ast.unparse(keyword.value)
                    # Extract the actual string value if it's a string constant
                    string_value = None
                    if isinstance(keyword.value, ast.Constant) and isinstance(
                        keyword.value.value, str
                    ):
                        string_value = keyword.value.value

                    # Skip excluded hardcoded classes
                    if string_value not in EXCLUDE_TCSS_CLASSES:
                        hardcoded_results.append(
                            HardcodedTcssData(
                                module_path=str(py_file),
                                line_number=keyword.lineno,
                                code=code_str,
                            )
                        )
    return hardcoded_results


@pytest.mark.parametrize(
    "py_file", get_modules_importing_class(class_name=CLASS_NAME), ids=lambda p: p.name
)
def test_no_hardcoded(py_file: Path) -> None:
    hardcoded = _check_file_for_hardcoded(py_file)
    if hardcoded:
        failures = "\n".join(
            f"{d.module_path}:{d.line_number} has {HARDCODED}: {d.code}"
            for d in hardcoded
        )
        pytest.fail(failures)
