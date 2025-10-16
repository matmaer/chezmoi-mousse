import ast
import pathlib

import pytest
from _test_utils import get_module_ast_tree, get_module_paths


def get_module_exports(module_path: pathlib.Path) -> set[str]:
    """Get the list of names exported by a module via __all__."""
    try:
        tree = get_module_ast_tree(module_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            exports: set[str] = set()
                            for elt in node.value.elts:
                                if isinstance(
                                    elt, ast.Constant
                                ) and isinstance(elt.value, str):
                                    exports.add(elt.value)
                            return exports
    except Exception:
        pass
    return set()


def resolve_relative_import(
    from_module_path: pathlib.Path, import_module: str, level: int
) -> pathlib.Path | None:
    """Resolve a relative import to an absolute module path."""
    if level == 0:  # Absolute import
        return None

    # Get the directory of the importing module
    current_dir = from_module_path.parent

    # Go up the directory tree based on the level
    target_dir = current_dir
    for _ in range(level - 1):
        target_dir = target_dir.parent

    # Get the module name
    if not import_module:
        return None

    # Convert module path to file path
    module_parts = import_module.split(".")
    target_path = target_dir
    for part in module_parts:
        target_path = target_path / part

    # Try .py file first, then __init__.py in directory
    if (target_path.with_suffix(".py")).exists():
        return target_path.with_suffix(".py")
    elif (target_path / "__init__.py").exists():
        return target_path / "__init__.py"

    return None


class ImportChecker(ast.NodeVisitor):
    def __init__(self, filepath: pathlib.Path, base_dir: pathlib.Path):
        self.filepath = filepath
        self.base_dir = base_dir
        self.errors: list[str] = []

    def visit_ImportFrom(self, node: ast.ImportFrom):
        # Check for direct imports from submodules (original test)
        if (
            node.module
            and node.module.startswith("chezmoi_mousse.")
            and node.module != "chezmoi_mousse"
        ):
            self.errors.append(
                f"Direct submodule import in {self.filepath.name}: from {node.module} import ..."
            )

        # Check for relative imports where names are not exported by the target module
        if node.module and node.level > 0:  # Only check relative imports
            target_module_path = resolve_relative_import(
                self.filepath, node.module, node.level
            )
            if target_module_path and target_module_path.exists():
                # Get what this target module exports
                exported_names = get_module_exports(target_module_path)

                # Check each imported name
                for alias in node.names:
                    import_name = alias.name
                    # Skip star imports
                    if import_name == "*":
                        continue
                    # If the target module has __all__ but doesn't export this name
                    if exported_names and import_name not in exported_names:
                        self.errors.append(
                            f"Relative import in {self.filepath.name}: "
                            f"'{import_name}' imported from {node.module} "
                            f"but not exported by {target_module_path.name}"
                        )

        self.generic_visit(node)


GUI_MODULE_PATHS = [
    pathlib.Path.cwd() / p for p in get_module_paths() if "gui" in str(p)
]


def test_indirect_imports():
    """Test all GUI modules for indirect imports at once to get a complete overview."""
    all_errors: list[str] = []
    base_dir = pathlib.Path(__file__).parent.parent / "src" / "chezmoi_mousse"

    for py_file in GUI_MODULE_PATHS:
        tree = get_module_ast_tree(py_file)
        checker = ImportChecker(py_file, base_dir)
        checker.visit(tree)
        all_errors.extend(checker.errors)

    if all_errors:
        pytest.fail("\n".join(all_errors))
