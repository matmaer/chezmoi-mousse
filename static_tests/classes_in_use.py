import ast
from typing import TYPE_CHECKING

import pytest
from static_tests._ast_nodes import NodeData, NodeDb

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


def get_class_issues(node_db: NodeDb) -> tuple[list[str], list[str]]:
    """Analyzes top-level classes for usage and privacy recommendations."""
    class_nodes: NDSet = node_db.by_type.get(ast.ClassDef.__name__, set())
    name_nodes: NDSet = node_db.by_type.get(ast.Name.__name__, set())

    # Map class_name -> top-level ClassDef NodeData
    defined_classes: dict[str, NodeData] = {}
    for node in class_nodes:
        assert isinstance(node.ast_node, ast.ClassDef)
        class_name = node.ast_node.name
        if node and class_name not in EXCLUDE_CLASSES:
            defined_classes[class_name] = node

    # Track usage files per class name
    class_file_usages: dict[str, set[str]] = {}

    for name_node in name_nodes:
        if (
            not isinstance(name_node.ast_node, ast.Name)
            or name_node.str_rep not in defined_classes
        ):
            continue

        # Ignore class definition headers (Store context)
        if isinstance(name_node.ast_node.ctx, ast.Store):
            continue

        class_name = name_node.str_rep
        class_node = defined_classes[class_name]

        # Ignore self-references inside the class definition itself
        if _is_inside_class(name_node, class_node):
            continue

        class_file_usages.setdefault(class_name, set()).add(name_node.rel_path)

    unused_classes: list[str] = []
    should_be_private: list[str] = []

    for class_name, class_node in defined_classes.items():
        file_usages = class_file_usages.get(class_name, set())
        is_private = class_name.startswith("_")
        loc_str = f"{class_node.rel_path}:{class_node.lineno}"

        if not file_usages:
            unused_classes.append(f"Class '{class_name}' is unused ({loc_str})")
        elif class_name in node_db.textual_subclass_names:
            continue
        if file_usages == {class_node.rel_path} and not is_private:
            should_be_private.append(
                f"Class '{class_name}' used only in defined file, should be private "
                f"({loc_str})"
            )

    return sorted(unused_classes), sorted(should_be_private)


def test_classes_in_use(node_db: NodeDb) -> None:
    unused, should_be_private = get_class_issues(node_db)
    reports: list[str] = []

    if unused:
        reports.append("Unused classes found:")
        reports.extend(f"- {item}" for item in unused)

    if should_be_private:
        reports.append("\nPublic classes that should be private:")
        reports.extend(f"- {item}" for item in should_be_private)

    if reports:
        pytest.fail("\n".join(reports))
