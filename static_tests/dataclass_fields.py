import ast
from typing import TYPE_CHECKING

from static_tests._ast_nodes import NodeData, NodeDb
from static_tests.conftest import CheckRunner, IssueList

if TYPE_CHECKING:
    from static_tests._ast_nodes import NDSet

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
            if child.node_type == "AnnAssign"
            and isinstance(child.ast_node, ast.AnnAssign)
            and isinstance(child.ast_node.target, ast.Name)
        }
        if fields:
            dataclass_fields[class_node] = fields

    return dataclass_fields


def _is_inside_class(attr: NodeData, class_node: NodeData) -> bool:
    """Walks the parent chain to check if an attribute node resides inside
    class_node or not."""
    curr: NodeData | None = attr.parent
    while curr:
        if curr == class_node:
            return True
        curr = curr.parent
    return False


def get_unused(node_db: NodeDb) -> IssueList:
    dataclass_fields: DcFieldDict = _extract_dataclass_fields(node_db)
    attr_nodes: NDSet = node_db.by_type.get(ast.Attribute.__name__, set())
    issue_list: IssueList = []

    for class_node, fields in dataclass_fields.items():
        assert isinstance(class_node.ast_node, ast.ClassDef)
        class_name = class_node.ast_node.name

        field_names = {f.dc_field_name for f in fields}
        used_externally: set[str] = set()
        used_internally: set[str] = set()

        for attr in attr_nodes:
            if (
                not isinstance(attr.ast_node, ast.Attribute)
                or attr.str_rep not in field_names
            ):
                continue

            field_name = attr.str_rep
            value_node = attr.ast_node.value

            if _is_inside_class(attr, class_node):
                if isinstance(value_node, ast.Name) and value_node.id == "self":
                    used_internally.add(field_name)
            else:
                used_externally.add(field_name)

        # Evaluate usage for each field
        for field_node in fields:
            loc_str = f"{class_node.rel_path}:{field_node.lineno}"
            field_name = field_node.dc_field_name

            if field_name in used_externally or (
                field_name.startswith("_") and field_name in used_internally
            ):
                continue
            if field_name in used_internally and not field_name.startswith("_"):
                issue_list.append(
                    (
                        f"{class_name}",
                        f"{field_name}",
                        f"{loc_str}",
                        "Member(s) can be private",
                    ),
                )
            else:
                issue_list.append(
                    (
                        f"{class_name}",
                        f"{field_name}",
                        f"{loc_str}",
                        "Member(s) not in use",
                    ),
                )
    return issue_list


def test_dataclass_fields(run_check: CheckRunner) -> None:
    run_check(get_unused)
