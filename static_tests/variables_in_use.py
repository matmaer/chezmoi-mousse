import ast
from typing import TYPE_CHECKING

from static_tests._ast_nodes import NodeData, NodeDb
from static_tests.conftest import CheckRunner, IssueList

if TYPE_CHECKING:
    from static_tests._ast_nodes import NDSet

# Ignore common framework hooks, special dunders, and Pytest variables
IGNORED_MODULE_VARS = {
    "__all__",
    "__doc__",
    "total_issues_count",
    "pytestmark",
}

# Known descriptor factory functions (Textual reactives, etc.)
DESCRIPTOR_FACTORIES = {"reactive", "var"}


def _find_enclosing_class(node: NodeData) -> str:
    """Walks parent chain to find enclosing ClassDef node if present."""
    current = node.parent
    while current:
        if current.node_type == "ClassDef":
            assert isinstance(current.ast_node, ast.ClassDef)
            return current.ast_node.name
        current = current.parent
    return ""


def _is_reactive_or_descriptor(assign_node: NodeData) -> bool:
    """Detects assignments like `foo = reactive(...)` or `bar: reactive[bool] =
    reactive(...)`."""
    ast_node = assign_node.ast_node
    val = getattr(ast_node, "value", None)
    if isinstance(val, ast.Call):
        if isinstance(val.func, ast.Name) and val.func.id in DESCRIPTOR_FACTORIES:
            return True
        if (
            isinstance(val.func, ast.Attribute)
            and val.func.attr in DESCRIPTOR_FACTORIES
        ):
            return True
    return False


def get_variable_issues(node_db: NodeDb) -> IssueList:
    """Analyzes module variables, class variables, and instance attributes for usage."""
    issue_list: IssueList = []
    assign_nodes: NDSet = set()
    for type_name in (ast.Assign.__name__, ast.AnnAssign.__name__):
        assign_nodes.update(node_db.by_type.get(type_name, set()))

    attr_nodes: NDSet = node_db.by_type.get(ast.Attribute.__name__, set())
    name_nodes: NDSet = node_db.by_type.get(ast.Name.__name__, set())

    # Collect exported names across all modules (__all__ = [...])
    exported_names: set[str] = set()
    for assign in assign_nodes:
        if assign.target_name == "__all__" and assign.export_names:
            exported_names.update(assign.export_names)

    module_vars: dict[str, NodeData] = {}
    class_vars: dict[tuple[str, str], NodeData] = {}
    instance_vars: dict[tuple[str, str], NodeData] = {}

    # 1. Gather Variable Definitions
    for assign_node in assign_nodes:
        var_name = assign_node.target_name
        if not var_name or var_name.startswith("_"):
            continue

        # Skip Textual reactives & descriptors (managed implicitly by Textual framework)
        if _is_reactive_or_descriptor(assign_node):
            continue

        enclosing: str = _find_enclosing_class(assign_node)

        if assign_node.is_top_level:
            if var_name not in IGNORED_MODULE_VARS and var_name not in exported_names:
                module_vars[var_name] = assign_node
        elif enclosing:
            # Class-level variable assignment
            if assign_node.parent and assign_node.parent.node_type == "ClassDef":
                # Ignore uppercase constants (e.g. ICON_NODE = "...") or annotated
                # type hints
                if not var_name.isupper():
                    class_vars[(enclosing, var_name)] = assign_node
            # Instance-level variable assignment (`self.x = ...`)
            elif assign_node.is_self_attribute:
                instance_vars[(enclosing, var_name)] = assign_node

    # 2. Track Load Context Usages Across Codebase
    loaded_module_vars: set[str] = set()
    loaded_attributes: set[str] = set()

    # Direct Name Loads (e.g. add_ids or from store import add_ids)
    for name_node in name_nodes:
        if name_node.is_load_context and name_node.target_name:
            var_name = name_node.target_name
            if not var_name.startswith("_"):
                loaded_module_vars.add(var_name)

    # Attribute Loads (e.g. store.add_ids or self.foo)
    for attr_node in attr_nodes:
        if attr_node.is_load_context and attr_node.target_name:
            attr_name = attr_node.target_name
            if not attr_name.startswith("_"):
                loaded_attributes.add(attr_name)

    # 3. Evaluate Module Variables
    for var_name, node in module_vars.items():
        if var_name not in loaded_module_vars and var_name not in loaded_attributes:
            issue_list.append(
                (
                    f"{var_name}",
                    f"{node.rel_path}:{node.lineno}",
                    "Module variable(s) never loaded",
                )
            )

    # 4. Evaluate Class Variables
    for (class_name, var_name), node in class_vars.items():
        if var_name not in loaded_attributes and var_name not in loaded_module_vars:
            issue_list.append(
                (
                    f"{var_name}",
                    f"{class_name}",
                    f"{node.rel_path}:{node.lineno}",
                    "Class variable(s) never loaded",
                )
            )

    # 5. Evaluate Instance Attributes (self.x)
    for (class_name, var_name), node in instance_vars.items():
        if var_name not in loaded_attributes:
            issue_list.append(
                (
                    f"{var_name}",
                    f"{class_name}",
                    f"{node.rel_path}:{node.lineno}",
                    "Instance attribute(s) never loaded",
                )
            )

    return issue_list


def test_variables(run_check: CheckRunner) -> None:
    run_check(get_variable_issues)
