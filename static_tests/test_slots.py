import ast
from pathlib import Path

import pytest
from _test_utils import get_module_ast_class_defs


def test_app_ids_slots() -> None:
    app_ids_path = Path("src/chezmoi_mousse/_app_ids.py")
    class_defs = get_module_ast_class_defs(app_ids_path)

    for class_def in class_defs:
        if class_def.name != "AppIds":
            continue

        slots: set[str] = set()
        for stmt in class_def.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id == "__slots__"
                        and isinstance(stmt.value, (ast.Tuple, ast.List))
                    ):
                        for elt in stmt.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(
                                elt.value, str
                            ):
                                slots.add(elt.value)

        assigned_attrs: set[str] = set()
        for stmt in class_def.body:
            if isinstance(stmt, ast.FunctionDef):
                for node in ast.walk(stmt):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Attribute) and (
                                isinstance(target.value, ast.Name)
                                and target.value.id == "self"
                            ):
                                assigned_attrs.add(target.attr)

        unassigned_slots = slots - assigned_attrs
        if unassigned_slots:
            pytest.fail(
                "\nAppIds has slots never assigned in its methods: "
                f"{', '.join(unassigned_slots)}"
            )
