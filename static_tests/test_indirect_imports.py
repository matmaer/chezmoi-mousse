import ast
from pathlib import Path

import pytest
from _test_utils import get_module_ast_tree, get_module_paths

GUI_MODULE_PATHS = [Path.cwd() / p for p in get_module_paths() if "gui" in p.parts]


def get_module_exports(module_path: Path) -> set[str]:
    tree = get_module_ast_tree(module_path)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in node.targets
            )
            and isinstance(node.value, (ast.List, ast.Tuple))
        ):
            return {
                elt.value
                for elt in node.value.elts
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            }
    return set()


def resolve_relative_import(
    from_module_path: Path, import_module: str, level: int
) -> Path:
    # Go up the directory tree based on the level
    target_dir = from_module_path.parent
    for _ in range(level - 1):
        target_dir = target_dir.parent

    # Convert module path to file path
    module_parts = import_module.split(".")
    target_path = target_dir
    for part in module_parts:
        target_path = target_path / part

    return target_path.with_suffix(".py")


class ImportChecker(ast.NodeVisitor):
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.errors: list[str] = []

    def visit_ImportFrom(self, node: ast.ImportFrom):
        # Check for relative imports where names are not exported by the target module
        if not (node.module and node.level > 0):  # Only check relative imports
            return self.generic_visit(node)

        target_module_path = resolve_relative_import(
            self.filepath, node.module, node.level
        )
        exported_names = get_module_exports(target_module_path)

        if not exported_names:
            pytest.skip(
                f"Target module {target_module_path.name} has no __all__ definition, skipping import validation"
            )

        # Check each imported name
        for alias in node.names:
            if alias.name != "*" and alias.name not in exported_names:
                self.errors.append(
                    f"Relative import in {self.filepath.name} at line {node.lineno}: "
                    f"'{alias.name}' imported from {node.module} "
                    f"but not exported by {target_module_path.name}"
                )

        self.generic_visit(node)


@pytest.mark.parametrize("module_path", GUI_MODULE_PATHS, ids=lambda p: p.stem)
def test_indirect_imports(module_path: Path):
    checker = ImportChecker(module_path)
    checker.visit(get_module_ast_tree(module_path))
    if checker.errors:
        pytest.fail("\n".join(checker.errors))
