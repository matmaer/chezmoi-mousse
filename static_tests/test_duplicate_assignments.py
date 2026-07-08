import ast
from pathlib import Path

import pytest


def find_duplicate_assignments_in_class(
    class_def: ast.ClassDef,
) -> dict[tuple[str, str], list[int]]:
    assignments: dict[tuple[str, str], list[int]] = {}
    instance_var_assignments: dict[tuple[str, str], dict[str, list[int]]] = {}

    def collect_assignments(
        nodes: list[ast.stmt], method_name: str | None = None
    ) -> None:
        for item in nodes:
            if isinstance(item, ast.Assign) and len(item.targets) == 1:
                target = item.targets[0]
                attr_name = None
                is_instance_var = False

                # Check for self.x = value assignments
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    attr_name = target.attr
                    is_instance_var = True

                # Check for x = value assignments
                elif isinstance(target, ast.Name):
                    attr_name = target.id

                if attr_name and not any(
                    isinstance(node, ast.Call) for node in ast.walk(item.value)
                ):
                    value_str = ast.unparse(item.value)
                    key = (attr_name, value_str)

                    if is_instance_var and method_name:
                        # Track instance variables by method
                        instance_var_assignments.setdefault(key, {}).setdefault(
                            method_name, []
                        ).append(item.lineno)
                    else:
                        # Regular assignments (non-instance or class-level)
                        assignments.setdefault(key, []).append(item.lineno)
            elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                collect_assignments(item.body, item.name)

    collect_assignments(class_def.body)

    # Only report instance variable duplicates within the same method
    for key, methods in instance_var_assignments.items():
        for line_numbers in methods.values():
            if len(line_numbers) > 1:
                assignments.setdefault(key, []).extend(line_numbers)

    return assignments


def test_duplicate_assignments() -> None:
    src_dir = Path(__file__).parent.parent / "src"
    py_files = list(src_dir.rglob("*.py"))
    failures: list[str] = []

    for file_path in py_files:
        relative_path = file_path.relative_to(src_dir.parent)
        tree = ast.parse(file_path.read_text(encoding="utf-8"))

        # Walk the AST to find all class definitions within the file
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                assignments = find_duplicate_assignments_in_class(node)
                dup_lines = [
                    line_num
                    for line_numbers in assignments.values()
                    if len(line_numbers) > 1
                    for line_num in line_numbers
                ]
                if dup_lines:
                    sorted_lines = sorted(set(dup_lines))
                    failures.append(
                        f"{relative_path}: {node.name} (line {node.lineno}) "
                        f"has duplicate assignments at lines: {sorted_lines}"
                    )

    if failures:
        pytest.fail("Duplicate assignments found:\n" + "\n".join(failures))
