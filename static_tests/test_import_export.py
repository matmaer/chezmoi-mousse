import ast
from pathlib import Path

import pytest
from _test_utils import (
    get_exported_names,
    get_gui_module_paths,
    get_module_ast_class_defs,
    get_module_ast_tree,
    get_module_paths,
    get_modules_importing_class,
)

INIT_PATH = Path("src", "chezmoi_mousse", "__init__.py")
PACKAGE_NAME = "chezmoi_mousse"


def get_gui_imports_from_package() -> set[str]:
    # Collect all names imported via 'from chezmoi_mousse import ...' in the gui folder
    names: set[str] = set()
    for py_file in get_gui_module_paths():
        tree = get_module_ast_tree(py_file)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == PACKAGE_NAME:
                for alias in node.names:
                    names.add(alias.name)
    return names


def test_init_exports() -> None:
    # __all__ in __init__.py should match what gui files import from chezmoi_mousse
    gui_imports = get_gui_imports_from_package()
    exported = get_exported_names(INIT_PATH)

    exported_names = exported - {"__version__"}
    errors: list[str] = []

    never_used = exported_names - gui_imports
    if never_used:
        errors.append(
            f"Exported in __all__ but never imported in gui: {sorted(never_used)}"
        )

    not_exported = gui_imports - exported
    if not_exported:
        errors.append(
            f"Imported in gui but missing from chezmoi_mousse.__all__: "
            f"{sorted(not_exported)}"
        )

    if errors:
        pytest.fail("\n".join(errors))


def get_modules_to_test() -> list[Path]:
    # Get modules that have classes imported elsewhere.
    modules_to_test: list[Path] = []

    for module_path in get_module_paths():
        class_defs = get_module_ast_class_defs(module_path)
        if not class_defs:
            continue

        # Check if any class from this module is imported elsewhere
        for class_def in class_defs:
            if get_modules_importing_class(class_def.name):
                modules_to_test.append(module_path)
                break  # Only need to add the module once

    return modules_to_test


@pytest.mark.parametrize(
    "module_path", get_modules_to_test(), ids=lambda module_path: module_path.name
)
def test_module_exports(module_path: Path):
    # Test that a module exports all classes that are imported elsewhere,
    # and that exported classes are imported elsewhere
    class_defs = get_module_ast_class_defs(module_path)
    defined_classes = {cls.name: cls.lineno for cls in class_defs}

    # Find which of these classes are actually imported elsewhere
    imported_classes = {
        cls_name
        for cls_name in defined_classes
        if get_modules_importing_class(cls_name)
    }
    exported = get_exported_names(module_path)

    errors: list[str] = []

    # Check if imported classes are exported
    if imported_classes:
        if not exported:
            errors.append(
                f"{module_path.name}: no __all__ but has classes imported in gui: "
                f"{sorted(imported_classes)}"
            )
        else:
            missing = imported_classes - exported
            if missing:
                errors.append(
                    f"{module_path.name} missing from __all__: {sorted(missing)}"
                )

    # Check if exported classes are imported elsewhere
    if exported:
        # Assume all exported names except __version__ are classes
        classes_exported = (
            exported - {"__version__"} if "__version__" in exported else exported
        )
        never_imported = [
            cls for cls in classes_exported if not get_modules_importing_class(cls)
        ]
        if never_imported:
            for cls in never_imported:
                line_info = (
                    f":{defined_classes.get(cls, 'unknown')}"
                    if cls in defined_classes
                    else ""
                )
                errors.append(
                    f"{module_path.name} exports {cls}{line_info} but never imported"
                )

    if errors:
        pytest.fail("\n".join(errors))


########################################
# Test Indirect Imports in GUI Modules #
########################################


@pytest.mark.parametrize("module_path", get_gui_module_paths(), ids=lambda p: p.name)
def test_indirect_imports(module_path: Path):
    checker = ImportChecker(module_path)
    checker.visit(get_module_ast_tree(module_path))
    if checker.errors:
        pytest.fail("\n".join(checker.errors))


class ImportChecker(ast.NodeVisitor):
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.errors: list[str] = []

    def visit_ImportFrom(self, node: ast.ImportFrom):

        def resolve_relative_import(
            from_module_path: Path, import_module: str, level: int
        ) -> Path:
            # Go up the directory tree based on the level
            target_dir = from_module_path.parents[level - 1]

            # Convert module path to file path
            module_parts = import_module.split(".")
            return target_dir.joinpath(*module_parts).with_suffix(".py")

        # Check for relative imports where names are not exported by the target module
        if not (node.module and node.level > 0):  # Only check relative imports
            return self.generic_visit(node)

        exported_names = get_exported_names(
            resolve_relative_import(self.filepath, node.module, node.level)
        )

        if not exported_names:
            # If the module exists but has no __all__, we can't validate the import
            return self.generic_visit(node)

        # Check each imported name
        for alias in node.names:
            if alias.name not in exported_names:
                self.errors.append(
                    f"{self.filepath.name} imports {alias.name} "
                    f"but not exported by {node.module}"
                )

        self.generic_visit(node)
