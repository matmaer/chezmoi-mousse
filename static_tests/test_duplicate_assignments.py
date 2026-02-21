import ast
from pathlib import Path

import pytest
from _test_utils import get_module_ast_class_defs, get_module_paths


def find_duplicate_assignments_in_class(
    class_def: ast.ClassDef,
) -> dict[tuple[str, str], list[int]]:
    assignments: dict[tuple[str, str], list[int]] = {}

    def collect_assignments(nodes: list[ast.stmt]) -> None:
        # Recursively collect self.x = value and x = value assignments
        for item in nodes:
            if isinstance(item, ast.Assign):
                if len(item.targets) == 1:
                    target = item.targets[0]
                    attr_name = None

                    # Check for self.x = value assignments
                    if (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "self"
                    ):
                        attr_name = target.attr
                    # Check for x = value assignments
                    elif isinstance(target, ast.Name):
                        attr_name = target.id

                    if attr_name:
                        value_str = ast.unparse(item.value)
                        key = (attr_name, value_str)
                        assignments.setdefault(key, []).append(item.lineno)
            elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Recurse into function bodies (e.g., __init__)
                collect_assignments(item.body)

    collect_assignments(class_def.body)
    return assignments


@pytest.mark.parametrize("file_path", get_module_paths(), ids=lambda p: p.name)
def test_duplicate_assignments(file_path: Path) -> None:
    failures: list[str] = []
    for class_def in get_module_ast_class_defs(file_path):
        assignments = find_duplicate_assignments_in_class(class_def)
        dup_lines = [
            line_num
            for line_numbers in assignments.values()
            if len(line_numbers) > 1
            for line_num in line_numbers
        ]
        if dup_lines:
            failures.append(
                f"{class_def.name} (line {class_def.lineno}) has duplicate assignments at lines: {sorted(set(dup_lines))}"
            )
    if failures:
        pytest.fail("\n".join(failures))
