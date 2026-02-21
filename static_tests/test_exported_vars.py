import ast
from pathlib import Path

import pytest
from _test_utils import (
    get_module_ast_class_defs,
    get_module_ast_tree,
    get_module_paths,
    get_modules_importing_class,
)

INIT_PATH = Path("src", "chezmoi_mousse", "__init__.py")
GUI_DIR = Path("src", "chezmoi_mousse", "gui")
PACKAGE_NAME = "chezmoi_mousse"


def get_gui_imports_from_package() -> set[str]:
    # Collect all names imported via 'from chezmoi_mousse import ...' in the gui folder.
    names: set[str] = set()
    for py_file in GUI_DIR.glob("**/*.py"):
        tree = ast.parse(py_file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == PACKAGE_NAME:
                for alias in node.names:
                    names.add(alias.name)
    return names


def test_init_exports() -> None:
    # __all__ in __init__.py should match exactly what gui files import from chezmoi_mousse.
    gui_imports = get_gui_imports_from_package()
    exported, _ = get_exported_names(INIT_PATH)

    if exported is None:
        pytest.fail("__init__.py has no __all__")
        return

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
            f"Imported from chezmoi_mousse in gui but missing from __all__: {sorted(not_exported)}"
        )

    if errors:
        pytest.fail("\n".join(errors))


def get_exported_names(module_path: Path) -> tuple[set[str] | None, int | None]:
    # Extract __all__ exports from a module and its line number.
    tree = get_module_ast_tree(module_path)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets
        ):
            if isinstance(node.value, ast.List):
                try:
                    exported = {
                        e.value
                        for e in node.value.elts
                        if isinstance(e, ast.Constant) and isinstance(e.value, str)
                    }
                    return exported, node.lineno
                except AttributeError:
                    return None, None
    return None, None


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
    "module_path", get_modules_to_test(), ids=lambda module_path: module_path.stem
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
    exported, all_lineno = get_exported_names(module_path)

    errors: list[str] = []

    # Check if imported classes are exported
    if imported_classes:
        if exported is None:
            errors.append(
                f"Module {module_path.stem} has no __all__ but exports classes: {sorted(imported_classes)}"
            )
        else:
            missing = imported_classes - exported
            if missing:
                line_info = f":{all_lineno}" if all_lineno else ""
                errors.append(
                    f"Module {module_path.stem}{line_info} missing from __all__: {sorted(missing)}"
                )

    # Check if exported classes are imported elsewhere
    if exported is not None:
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
                    f"Module {module_path.stem} exports class {cls}{line_info} never imported"
                )

    if errors:
        pytest.fail("\n".join(errors))
