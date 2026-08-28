import ast
from collections.abc import Callable

# State tracking across full repository walk
defined_slots: dict[tuple[str, str], tuple[str, int]] = {}
assigned_inside: set[tuple[str, str]] = set()
slot_usages: dict[str, set[str | None]] = {}


# Scope context state maintained during traversal
current_class: str | None = None
current_function: str | None = None


def get_rule_data(node: ast.AST, file_path: str) -> None:
    global current_class, current_function, defined_slots, assigned_inside, slot_usages
    # Track active class scope
    if isinstance(node, ast.ClassDef):
        prev_class = current_class
        current_class = node.name

        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == "__slots__":
                        _process_slots_value(
                            node.name, stmt.value, file_path, stmt.lineno
                        )
            elif isinstance(stmt, ast.AnnAssign) and (
                isinstance(stmt.target, ast.Name)
                and stmt.target.id == "__slots__"
                and stmt.value
            ):
                _process_slots_value(node.name, stmt.value, file_path, stmt.lineno)

        # Reset scope back when leaving class definition
        current_class = prev_class

    # Track active function scope inside class
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        current_function = node.name

    # Track attribute accesses / assignments
    elif isinstance(node, ast.Attribute):
        if (
            current_class
            and current_function
            and isinstance(node.ctx, ast.Store)
            and isinstance(node.value, ast.Name)
            and node.value.id == "self"
        ):
            assigned_inside.add((current_class, node.attr))

        slot_usages.setdefault(node.attr, set()).add(current_class)

    # No return value needed during traversal pass
    return None


def get_issues() -> list[str]:
    """Calculates and returns aggregated issues after traversal completes."""
    unassigned_slots: list[str] = []
    unused_outside_slots: list[str] = []

    for (class_name, slot_name), (file, line) in defined_slots.items():
        info_str = f"{slot_name} in {class_name} ({file}:{line})"
        usages = slot_usages.get(slot_name, set())
        outside_usages = usages - {class_name}
        is_assigned_internally = (class_name, slot_name) in assigned_inside

        if not is_assigned_internally and not outside_usages:
            unassigned_slots.append(info_str)

        if not outside_usages:
            unused_outside_slots.append(info_str)

    error_lines: list[str] = []
    if unassigned_slots:
        error_lines.append(
            "Found slots defined but never assigned inside or outside the class:"
        )
        error_lines.extend(f"- {item}" for item in unassigned_slots)

    if unused_outside_slots:
        error_lines.append("Found slots never used outside the class:")
        error_lines.extend(f"- {item}" for item in unused_outside_slots)

    return error_lines


def _process_slots_value(
    class_name: str, value_node: ast.AST, file_path: str, lineno: int
) -> None:
    slots_elements: list[str] = []
    if isinstance(value_node, (ast.Tuple, ast.List)):
        for elt in value_node.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                slots_elements.append(elt.value)
    elif isinstance(value_node, ast.Dict):
        for key in value_node.keys:
            if key and isinstance(key, ast.Constant) and isinstance(key.value, str):
                slots_elements.append(key.value)
    elif isinstance(value_node, ast.Constant) and isinstance(value_node.value, str):
        slots_elements.append(value_node.value)

    for slot in slots_elements:
        defined_slots[(class_name, slot)] = (file_path, lineno)


def test_slots_usage(run_ast_rule: Callable[..., list[str]]) -> None:
    run_ast_rule()
