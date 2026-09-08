import ast
from typing import TYPE_CHECKING

from static_tests._ast_nodes import NodeData, NodeDb
from static_tests.conftest import CheckRunner, IssueList

if TYPE_CHECKING:
    from static_tests._ast_nodes import NDSet

# Classes excluded from unused checks (e.g. monkey patches or debug utilities)
EXCLUDE_CLASSES = {"ClassInstanceTracker", "DebugLog"}


def _is_inside_class(node: NodeData, class_node: NodeData) -> bool:
    """Walks the parent chain to check if a node resides inside class_node."""
    curr: NodeData | None = node.parent
    while curr:
        if curr == class_node:
            return True
        curr = curr.parent
    return False


def get_class_issues(node_db: NodeDb) -> IssueList:
    """Analyzes top-level and nested classes for usage and privacy recommendations."""
    class_nodes: NDSet = node_db.by_type.get(ast.ClassDef.__name__, set())

    # Query both Name and Attribute nodes to catch accesses like
    # ConfigTab.CatConfigStatic
    name_nodes: NDSet = node_db.by_type.get(ast.Name.__name__, set())
    attr_nodes: NDSet = node_db.by_type.get(ast.Attribute.__name__, set())
    identifier_nodes = name_nodes | attr_nodes

    issue_list: IssueList = []

    # Map class_name -> ClassDef NodeData
    defined_classes: dict[str, NodeData] = {}
    for node in class_nodes:
        assert isinstance(node.ast_node, ast.ClassDef)
        class_name = node.ast_node.name
        if node and class_name not in EXCLUDE_CLASSES:
            defined_classes[class_name] = node

    # Track usage files per class name
    class_file_usages: dict[str, set[str]] = {}

    for identifier_node in identifier_nodes:
        # Extract name depending on whether it's ast.Name or ast.Attribute
        identifier_str = identifier_node.str_rep

        if not identifier_str or identifier_str not in defined_classes:
            continue

        # Ignore class definition headers (Store context on targets/assignments)
        if (
            identifier_node.ast_node
            and getattr(identifier_node.ast_node, "ctx", None) is ast.Store()
        ):
            continue

        class_name = identifier_str
        class_node = defined_classes[class_name]

        # Ignore self-references inside the class definition itself
        if _is_inside_class(identifier_node, class_node):
            continue

        class_file_usages.setdefault(class_name, set()).add(identifier_node.rel_path)

    for class_name, class_node in defined_classes.items():
        file_usages = class_file_usages.get(class_name, set())
        is_private = class_name.startswith("_")
        loc_str = f"{class_node.rel_path}:{class_node.lineno}"

        if not file_usages:
            issue_list.append(
                (
                    f"{class_name}",
                    f"{loc_str}",
                    "Unused class(es)",
                )
            )
        elif class_name in node_db.textual_subclass_names:
            continue
        if file_usages == {class_node.rel_path} and not is_private:
            issue_list.append(
                (
                    f"{class_name}",
                    f"{loc_str}",
                    "Class(es) can be private",
                )
            )

    return issue_list


def test_classes_in_use(run_check: CheckRunner) -> None:
    run_check(get_class_issues)
