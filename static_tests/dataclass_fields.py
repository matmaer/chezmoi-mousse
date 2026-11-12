import ast

import pytest
from static_tests._ast_nodes import NodeData, NodeDb, format_issues

type DcFieldDict = dict[NodeData, set[NodeData]]


def _extract_dataclass_fields(node_db: NodeDb) -> DcFieldDict:
    """Finds all dataclass nodes and maps each class to its defined fields."""
    dataclass_fields: DcFieldDict = {}

    class_nodes = node_db.by_type.get(ast.ClassDef.__name__, set())
    for class_node in class_nodes:
        if "dataclass" not in class_node.decorator_names:
            continue

        fields = {
            child
            for child in class_node.children
            if isinstance(child.ast_node, ast.AnnAssign)
            and isinstance(child.ast_node.target, ast.Name)
        }
        if fields:
            dataclass_fields[class_node] = fields

    return dataclass_fields


def get_unused(node_db: NodeDb) -> list[tuple[str, str, str]]:
    issue_list: list[tuple[str, str, str]] = []

    for class_node, fields in _extract_dataclass_fields(node_db).items():
        assert isinstance(class_node.ast_node, ast.ClassDef)
        class_name = class_node.ast_node.name

        for field_node in fields:
            field_name = field_node.dc_field_name
            attr_nodes = [
                n
                for n in node_db.by_name.get(field_name, set())
                if isinstance(n.ast_node, ast.Attribute)
            ]
            used_internally = any(n.is_inside(class_node) for n in attr_nodes)
            used_externally = any(not n.is_inside(class_node) for n in attr_nodes)
            is_private = field_name.startswith("_")

            if used_externally or (is_private and used_internally):
                continue

            name = f"{class_name}.{field_name}"
            loc_str = f"{class_node.rel_path}:{field_node.lineno}"
            if used_internally:
                issue_list.append((name, loc_str, "Member(s) can be private"))
            else:
                issue_list.append((name, loc_str, "Member(s) not in use"))
    return issue_list


def test_dataclass_fields(node_db: NodeDb) -> None:
    issues = get_unused(node_db)
    if issues:
        pytest.fail(format_issues(issues))
