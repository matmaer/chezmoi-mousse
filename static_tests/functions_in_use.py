import ast
from typing import TYPE_CHECKING

import pytest
from static_tests._ast_nodes import NodeData, NodeDb

if TYPE_CHECKING:
    from static_tests._ast_nodes import NDSet

# Classes whose methods are exempt from unused checks
EXCLUDE_CLASSES = {"DebugLog", "CustomScrollBarRender"}

# General Textual lifecycle & handler prefixes/names
TEXTUAL_LIFECYCLE_NAMES = {
    "compose",
    "render",
    "render_line",
    "render_lines",
    "filter_paths",
    "check_action",
}

TEXTUAL_LIFECYCLE_PREFIXES = (
    "action_",
    "watch_",
    "on_",
    "validate_",
    "compute_",
)


def _is_textual_subclass(class_node: NodeData, textual_imports: set[str]) -> bool:
    """Checks if a ClassDef node inherits from any dynamically imported Textual base
    class."""
    assert isinstance(class_node.ast_node, ast.ClassDef)
    for base in class_node.ast_node.bases:
        if isinstance(base, ast.Name) and base.id in textual_imports:
            return True
        elif isinstance(base, ast.Subscript) and isinstance(base.value, ast.Name):
            if base.value.id in textual_imports:
                return True
        elif isinstance(base, ast.Attribute) and base.attr in textual_imports:
            return True
    return False


def _is_textual_lifecycle_method(method_name: str) -> bool:
    """Checks if a method name matches common Textual callback/event naming
    conventions."""
    if method_name in TEXTUAL_LIFECYCLE_NAMES:
        return True
    return method_name.startswith(TEXTUAL_LIFECYCLE_PREFIXES)


def _find_enclosing_class(node: NodeData) -> str:
    curr = node.parent
    while curr:
        if curr.node_type == "ClassDef":
            assert isinstance(curr.ast_node, ast.ClassDef)
            return curr.ast_node.name
        curr = curr.parent
    return "module"


def get_function_issues(node_db: NodeDb) -> tuple[list[str], list[str]]:
    textual_imports = node_db.textual_imports

    func_type_names = (ast.FunctionDef.__name__, ast.AsyncFunctionDef.__name__)
    func_nodes: NDSet = set()
    for name in func_type_names:
        func_nodes.update(node_db.by_type.get(name, set()))

    attr_nodes: NDSet = node_db.by_type.get(ast.Attribute.__name__, set())
    name_nodes: NDSet = node_db.by_type.get(ast.Name.__name__, set())

    # 1. Gather Top-Level Module Functions
    module_functions: dict[str, NodeData] = {}
    for node in func_nodes:
        if node.is_top_level and not node.is_special_dunder:
            module_functions[node.function_name] = node

    # 2. Gather Class Methods
    class_methods: dict[tuple[str, str], tuple[NodeData, NodeData]] = {}

    for node in func_nodes:
        if node.is_special_dunder:
            continue

        parent = node.parent
        if parent and parent.node_type == "ClassDef":
            assert isinstance(parent.ast_node, ast.ClassDef)
            class_name = parent.ast_node.name

            if class_name in EXCLUDE_CLASSES:
                continue

            method_name = node.function_name

            # Skip Textual's @on decorated methods
            if node.decorator_name == "on":
                continue

            # Automatically skip Textual lifecycle methods in Textual subclasses
            if _is_textual_subclass(
                parent, textual_imports
            ) and _is_textual_lifecycle_method(method_name):
                continue

            class_methods[(class_name, method_name)] = (node, parent)

    # 3. Track Usages
    module_func_file_usages: dict[str, set[str]] = {}
    method_class_usages: dict[str, set[str]] = {}

    # Attribute accesses
    for attr_node in attr_nodes:
        assert isinstance(attr_node.ast_node, ast.Attribute)
        method_name = attr_node.ast_node.attr
        enclosing_class = _find_enclosing_class(attr_node)

        method_class_usages.setdefault(method_name, set()).add(enclosing_class)
        module_func_file_usages.setdefault(method_name, set()).add(attr_node.rel_path)

    # Name references
    for name_node in name_nodes:
        assert isinstance(name_node.ast_node, ast.Name)

        if isinstance(name_node.ast_node.ctx, ast.Store):
            continue

        identifier = name_node.ast_node.id
        enclosing_class = _find_enclosing_class(name_node)

        module_func_file_usages.setdefault(identifier, set()).add(name_node.rel_path)
        method_class_usages.setdefault(identifier, set()).add(enclosing_class)

    unused_functions: list[str] = []
    should_be_private: list[str] = []

    # 4. Evaluate Module Functions
    for func_name, node in module_functions.items():
        file_usages = module_func_file_usages.get(func_name, set())
        is_private = func_name.startswith("_")
        loc_str = f"{node.rel_path}:{node.lineno}"

        if not file_usages:
            unused_functions.append(f"Function '{func_name}()' is unused ({loc_str})")
        elif file_usages == {node.rel_path} and not is_private:
            should_be_private.append(
                f"Function '{func_name}()' used only in defined file, can be "
                f"private ({loc_str})"
            )

    # 5. Evaluate Class Methods
    for (class_name, method_name), (node, _class_node) in class_methods.items():
        class_usages = method_class_usages.get(method_name, set())
        is_private = method_name.startswith("_")
        loc_str = f"{node.rel_path}:{node.lineno}"

        if not class_usages:
            unused_functions.append(f"{method_name}() from {class_name} ({loc_str})")
        elif class_usages == {class_name} and not is_private:
            should_be_private.append(f"{method_name}() from {class_name} ({loc_str})")

    return sorted(unused_functions), sorted(should_be_private)


def test_functions_in_use(node_db: NodeDb) -> None:
    unused, should_be_private = get_function_issues(node_db)
    reports: list[str] = ["Function usage report:\n"]

    if unused:
        reports.append("\nUnused functions/methods found:\n")
        reports.extend(f"{item}" for item in unused)

    if should_be_private:
        reports.append("\nPublic functions/methods that can be private:\n")
        reports.extend(f"{item}" for item in should_be_private)

    if reports:
        pytest.fail("\n".join(reports))
