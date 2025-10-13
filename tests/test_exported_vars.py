import ast
from pathlib import Path

import pytest
from _test_utils import (
    get_module_ast_class_defs,
    get_module_ast_tree,
    get_module_paths,
    get_modules_importing_class,
)


def get_exported_names(module_path: Path) -> set[str] | None:
    # Extract __all__ exports from a module.
    tree = get_module_ast_tree(module_path)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets
        ):
            if isinstance(node.value, (ast.List, ast.Tuple)):
                try:
                    return {
                        e.value
                        for e in node.value.elts
                        if isinstance(e, ast.Constant)
                        and isinstance(e.value, str)
                    }
                except AttributeError:
                    return None
    return None


def get_modules_to_test() -> list[Path]:
    # Get modules that have classes imported elsewhere.
    modules_to_test = []

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
    "module_path",
    get_modules_to_test(),
    ids=lambda module_path: module_path.stem,
)
def test_module_exports_imported_classes(module_path):
    # Test that a module exports all classes that are imported elsewhere
    # Get classes defined in this module
    class_defs = get_module_ast_class_defs(module_path)
    defined_classes = {cls.name for cls in class_defs}

    # Find which of these classes are actually imported elsewhere
    imported_classes = {
        cls_name
        for cls_name in defined_classes
        if get_modules_importing_class(cls_name)
    }

    # Get exported names
    exported = get_exported_names(module_path)

    if exported is None:
        msg = f"Module {module_path.stem} has no __all__ but exports classes: {sorted(imported_classes)}"
    else:
        missing = imported_classes - exported
        if missing:
            msg = f"Module {module_path.stem} missing from __all__: {sorted(missing)}"
        else:
            return  # Test passes

    pytest.fail(f"{msg}\n  File: {module_path}")
