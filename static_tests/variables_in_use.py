import ast
from typing import TYPE_CHECKING

import pytest
from static_tests._ast_nodes import NodeData, NodeDb

if TYPE_CHECKING:
    from static_tests._ast_nodes import NDSet

# Known Textual base classes whose class-level overrides should be ignored automatically
TEXTUAL_BASE_CLASSES = {
    "App",
    "Screen",
    "Widget",
    "Tree",
    "Static",
    "Header",
    "Footer",
    "DirectoryTree",
    "DataTable",
    "Input",
    "Button",
    "Label",
    "RichLog",
    "OptionList",
    "SelectionList",
    "Tabs",
    "TabbedContent",
    "LoadingIndicator",
    "ProgressBar",
}


def _is_textual_subclass(class_node: NodeData) -> bool:
    """Checks if a ClassDef node inherits from a known Textual base class or generic
    (e.g. Tree[Path])."""
    assert isinstance(class_node.ast_node, ast.ClassDef)
    for base in class_node.ast_node.bases:
        # Match standard bases: class MyWidget(Widget):
        if isinstance(base, ast.Name) and base.id in TEXTUAL_BASE_CLASSES:
            return True
        # Match generic bases: class ManagedTree(Tree[Path]):
        elif isinstance(base, ast.Subscript) and isinstance(base.value, ast.Name):
            if base.value.id in TEXTUAL_BASE_CLASSES:
                return True
        # Match attribute bases: class MyWidget(widgets.Widget):
        elif isinstance(base, ast.Attribute) and base.attr in TEXTUAL_BASE_CLASSES:
            return True
    return False


def _find_enclosing_class(node: NodeData) -> tuple[str, NodeData] | None:
    """Walks parent chain to find enclosing ClassDef node if present."""
    curr = node.parent
    while curr:
        if curr.node_type == "ClassDef":
            assert isinstance(curr.ast_node, ast.ClassDef)
            return curr.ast_node.name, curr
        curr = curr.parent
    return None


def get_variable_issues(node_db: NodeDb) -> tuple[list[str], list[str]]:
    """Analyzes module variables, class variables, and instance attributes for ast.Load
    usage."""
    assign_nodes: NDSet = set()
    for type_name in (ast.Assign.__name__, ast.AnnAssign.__name__):
        assign_nodes.update(node_db.by_type.get(type_name, set()))

    attr_nodes: NDSet = node_db.by_type.get(ast.Attribute.__name__, set())
    name_nodes: NDSet = node_db.by_type.get(ast.Name.__name__, set())

    module_vars: dict[str, NodeData] = {}
    class_vars: dict[tuple[str, str], NodeData] = {}
    instance_vars: dict[tuple[str, str], NodeData] = {}

    # 1. Gather Variable Definitions
    for assign_node in assign_nodes:
        var_name = assign_node.target_name
        if not var_name or var_name.startswith("_"):
            continue

        enclosing = _find_enclosing_class(assign_node)

        if assign_node.is_top_level:
            module_vars[var_name] = assign_node
        elif enclosing is not None:
            class_name, class_node = enclosing

            # Class-level variable assignment
            if assign_node.parent and assign_node.parent.node_type == "ClassDef":
                # Automatically skip class variables in Textual subclasses
                if _is_textual_subclass(class_node):
                    continue
                class_vars[(class_name, var_name)] = assign_node

            # Instance-level variable assignment (`self.x = ...`)
            elif assign_node.is_self_attribute:
                instance_vars[(class_name, var_name)] = assign_node

    # 2. Track Load Context Usages Across Codebase
    loaded_module_vars: set[str] = set()
    loaded_attributes: set[str] = set()

    # Direct Name Loads
    for name_node in name_nodes:
        if name_node.is_load_context and name_node.target_name:
            var_name = name_node.target_name
            if not var_name.startswith("_"):
                loaded_module_vars.add(var_name)

    # Attribute Loads
    for attr_node in attr_nodes:
        if attr_node.is_load_context and attr_node.target_name:
            attr_name = attr_node.target_name
            if not attr_name.startswith("_"):
                loaded_attributes.add(attr_name)

    unused_variables: list[str] = []
    should_be_private: list[str] = []

    # 3. Evaluate Module Variables
    for var_name, node in module_vars.items():
        loc_str = f"{node.rel_path}:{node.lineno}"
        if var_name not in loaded_module_vars:
            unused_variables.append(
                f"Module variable '{var_name}' is never loaded ({loc_str})"
            )

    # 4. Evaluate Class Variables
    for (class_name, var_name), node in class_vars.items():
        loc_str = f"{node.rel_path}:{node.lineno}"
        if var_name not in loaded_attributes and var_name not in loaded_module_vars:
            unused_variables.append(
                f"Class variable '{class_name}.{var_name}' is never loaded ({loc_str})"
            )

    # 5. Evaluate Instance Attributes (self.x)
    for (class_name, var_name), node in instance_vars.items():
        loc_str = f"{node.rel_path}:{node.lineno}"
        if var_name not in loaded_attributes:
            unused_variables.append(
                f"Instance attribute '{class_name}.{var_name}' is never loaded "
                f"({loc_str})"
            )

    return sorted(unused_variables), sorted(should_be_private)


def test_variables_in_use(node_db: NodeDb) -> None:
    unused, should_be_private = get_variable_issues(node_db)
    reports: list[str] = []

    if unused:
        reports.append("Unused variables/attributes found (never loaded):")
        reports.extend(f"- {item}" for item in unused)

    if should_be_private:
        reports.append("\nPublic variables that should be private:")
        reports.extend(f"- {item}" for item in should_be_private)

    if reports:
        pytest.fail("\n".join(reports))
