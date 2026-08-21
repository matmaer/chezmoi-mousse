import ast

import pytest

from static_tests._cached_data import MODULE_DIR, ast_parse, get_file_paths


def find_duplicate_assignments_in_class(
    class_def: ast.ClassDef,
) -> dict[tuple[str, str], list[int]]:

    duplicates: dict[tuple[str, str], list[int]] = {}
    class_assignments: dict[tuple[str, str], list[int]] = {}
    method_assignments: dict[str, dict[tuple[str, str], list[int]]] = {}

    # Helper function to extract assignments from a list of statement nodes
    def scan_body(nodes: list[ast.stmt], method_name: str | None) -> None:
        for item in nodes:
            if isinstance(item, ast.Assign) and len(item.targets) == 1:
                target = item.targets[0]
                attr_name = None

                # Check self.x
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    attr_name = target.attr
                # Check x
                elif isinstance(target, ast.Name):
                    attr_name = target.id

                if attr_name and not any(
                    isinstance(node, ast.Call) for node in ast.walk(item.value)
                ):
                    value_str = ast.unparse(item.value)
                    key = (attr_name, value_str)

                    if method_name is not None:
                        # Dict per method to avoid cross-method false positives
                        method_assignments.setdefault(method_name, {}).setdefault(
                            key, []
                        ).append(item.lineno)
                    else:
                        class_assignments.setdefault(key, []).append(item.lineno)

            elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                scan_body(item.body, item.name)

    scan_body(class_def.body, None)

    # Collect class-level duplicate lines (must be duplicated at class-level)
    for key, line_numbers in class_assignments.items():
        if len(line_numbers) > 1:
            duplicates[key] = line_numbers

    # Collect method-level duplicate lines (must be duplicated within the same method)
    for _method_name, assignments in method_assignments.items():
        for key, line_numbers in assignments.items():
            if len(line_numbers) > 1:
                duplicates.setdefault(key, []).extend(line_numbers)

    return duplicates


def test_duplicate_assignments() -> None:

    failures: list[str] = []

    for file_path in get_file_paths():
        relative_path = file_path.relative_to(MODULE_DIR)
        tree = ast_parse(file_path)

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
