import ast
import pathlib

import pytest
from _test_utils import get_module_ast_tree, get_module_paths


class ImportChecker(ast.NodeVisitor):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.errors: list[str] = []

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if (
            node.module
            and node.module.startswith("chezmoi_mousse.")
            and node.module != "chezmoi_mousse"
        ):
            self.errors.append(
                f"Import from submodule in {self.filepath}: from {node.module} import ..."
            )
        self.generic_visit(node)


GUI_MODULE_PATHS = [
    pathlib.Path.cwd() / p for p in get_module_paths() if "gui" in str(p)
]
IDS = [
    str(
        p.relative_to(
            pathlib.Path(__file__).parent.parent / "src" / "chezmoi_mousse"
        )
    )
    for p in GUI_MODULE_PATHS
]


@pytest.mark.parametrize("py_file", GUI_MODULE_PATHS, ids=IDS)
def test_no_indirect_imports_in_gui_modules(py_file: pathlib.Path):
    errors: list[str] = []

    tree = get_module_ast_tree(py_file)

    checker = ImportChecker(str(py_file))
    checker.visit(tree)
    errors.extend(checker.errors)

    if errors:
        pytest.fail("\n".join(errors))
