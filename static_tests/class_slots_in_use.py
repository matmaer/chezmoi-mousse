import ast

import pytest

from static_tests._cached_data import MODULE_DIR, ast_parse, get_file_paths


class SlotsUsageDetector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.current_file: str = ""
        self.current_class: str | None = None
        self.current_function: str | None = None

        # Map of (class_name, slot_name) -> (file_path, lineno)
        self.defined_slots: dict[tuple[str, str], tuple[str, int]] = {}

        # Set of (class_name, slot_name) that are assigned to self inside class methods
        self.assigned_inside: set[tuple[str, str]] = set()

        # Map of slot_name -> set of class_names where it is accessed/assigned
        # (None represents global scope)
        self.slot_usages: dict[str, set[str | None]] = {}

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        # Save old class context to support nested classes perfectly
        old_class = self.current_class
        self.current_class = node.name

        for stmt in node.body:
            # Handle standard assignment: __slots__ = ...
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == "__slots__":
                        self._process_slots_value(node.name, stmt.value, stmt.lineno)
            # Handle annotated assignment: __slots__: tuple[str, ...] = ...
            elif isinstance(stmt, ast.AnnAssign) and (
                isinstance(stmt.target, ast.Name)
                and stmt.target.id == "__slots__"
                and stmt.value
            ):
                self._process_slots_value(node.name, stmt.value, stmt.lineno)

        self.generic_visit(node)
        self.current_class = old_class

    def _process_slots_value(
        self, class_name: str, value_node: ast.AST, lineno: int
    ) -> None:
        # Helper to extract string literals from tuple, list, dict, or constant variants
        # of __slots__
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
            self.defined_slots[(class_name, slot)] = (self.current_file, lineno)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        old_func = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_func

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        old_func = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_func

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # Check if this attribute access is an assignment context (ast.Store) on 'self'
        # inside an internal class method
        if (
            self.current_class
            and self.current_function
            and isinstance(node.ctx, ast.Store)
            and isinstance(node.value, ast.Name)
            and node.value.id == "self"
        ):
            self.assigned_inside.add((self.current_class, node.attr))

        # Track the context scope of where this slot name is being interacted with
        # (Load OR Store)
        self.slot_usages.setdefault(node.attr, set()).add(self.current_class)
        self.generic_visit(node)


def test_slots_usage() -> None:
    detector = SlotsUsageDetector()

    # Collect definitions and usages across the codebase
    for file_path in get_file_paths():
        detector.current_file = str(file_path.relative_to(MODULE_DIR))
        tree = ast_parse(file_path)
        detector.visit(tree)

    unassigned_slots: list[str] = []
    unused_outside_slots: list[str] = []

    for (class_name, slot_name), (file, line) in detector.defined_slots.items():
        info_str = f"{slot_name} in {class_name} ({file}:{line})"

        # Check if the slot is assigned inside its own class methods
        # OR assigned from outside
        usages = detector.slot_usages.get(slot_name, set())
        outside_usages = usages - {class_name}
        is_assigned_internally = (class_name, slot_name) in detector.assigned_inside

        # To see if it was assigned from outside, we would need complex object-type
        # tracking, but because any external usage (Load or Store) qualifies the slot as
        # "in use", we consider it safely covered under 'outside_usages' if it's
        # interacted with outside.
        if not is_assigned_internally and not outside_usages:
            unassigned_slots.append(info_str)

        # Check if the slot is ever used outside of its own class
        # (either reading or writing to it)
        if not outside_usages:
            unused_outside_slots.append(info_str)

    # Build a combined reporting block
    error_lines: list[str] = []

    if unassigned_slots:
        error_lines.append(
            "\nFound slots defined but never assigned inside or outside the class:"
        )
        error_lines.extend(f"- {item}" for item in unassigned_slots)

    if unused_outside_slots:
        error_lines.append("\nFound slots never used outside the class:")
        error_lines.extend(f"- {item}" for item in unused_outside_slots)

    if error_lines:
        pytest.fail("\n".join(error_lines))
