import ast
from typing import TYPE_CHECKING

from static_tests._ast_nodes import NodeData, NodeDb
from static_tests.conftest import CheckRunner

if TYPE_CHECKING:
    from static_tests._ast_nodes import NDSet

type EnumMembersDict = dict[NodeData, set[NodeData]]


def _extract_enum_members(node_db: NodeDb) -> EnumMembersDict:

    enum_members: EnumMembersDict = {}

    class_nodes = node_db.by_type.get(ast.ClassDef.__name__, set())
    for class_node in class_nodes:
        if not class_node.is_enum_class:
            continue

        members = {
            child
            for child in class_node.children
            if child.node_type == "Assign"
            and isinstance(child.ast_node, ast.Assign)
            and len(child.ast_node.targets) == 1
            and isinstance(child.ast_node.targets[0], ast.Name)
        }
        if members:
            enum_members[class_node] = members

    return enum_members


def _is_inside_class(node: NodeData, class_node: NodeData) -> bool:
    """Walks the parent chain to check if a node resides inside class_node."""
    curr: NodeData | None = node.parent
    while curr:
        if curr == class_node:
            return True
        curr = curr.parent
    return False


def _check_alternative_usage(
    node_db: NodeDb, class_name: str, member_names: set[str]
) -> set[str]:
    # Accounts for usage in loops or comprehensions
    for loop_type in (ast.For.__name__, ast.comprehension.__name__):
        for loop_node in node_db.by_type.get(loop_type, set()):
            ast_node = loop_node.ast_node
            assert isinstance(ast_node, (ast.For, ast.comprehension))
            if isinstance(ast_node.iter, ast.Name) and ast_node.iter.id == class_name:
                return set(member_names)

    # Subscript lookups: MyEnum["MEMBER_NAME"]
    used_members: set[str] = set()
    for sub_node in node_db.by_type.get(ast.Subscript.__name__, set()):
        assert isinstance(sub_node.ast_node, ast.Subscript)
        value = sub_node.ast_node.value
        slice_node = sub_node.ast_node.slice

        if (
            isinstance(value, ast.Name)
            and value.id == class_name
            and isinstance(slice_node, ast.Constant)
            and isinstance(slice_node.value, str)
            and slice_node.value in member_names
        ):
            used_members.add(slice_node.value)

    return used_members


def get_unused(node_db: NodeDb) -> list[tuple[str, ...]]:
    enum_members = _extract_enum_members(node_db)
    attr_nodes: NDSet = node_db.by_type.get(ast.Attribute.__name__, set())
    name_nodes: NDSet = node_db.by_type.get(ast.Name.__name__, set())
    unused_reports: list[tuple[str, ...]] = []

    for class_node, members in enum_members.items():
        assert isinstance(class_node.ast_node, ast.ClassDef)
        class_name = class_node.ast_node.name
        member_names = {m.enum_member_name for m in members}

        used_externally = _check_alternative_usage(node_db, class_name, member_names)
        used_internally: set[str] = set()

        # External member accesses: MyEnum.MEMBER
        for attr in attr_nodes:
            if (
                isinstance(attr.ast_node, ast.Attribute)
                and attr.str_rep in member_names
                and isinstance(attr.ast_node.value, ast.Name)
                and attr.ast_node.value.id == class_name
            ):
                used_externally.add(attr.str_rep)

        # Internal member references
        for name in name_nodes:
            if (
                isinstance(name.ast_node, ast.Name)
                and name.str_rep in member_names
                and isinstance(name.ast_node.ctx, ast.Load)
                and _is_inside_class(name, class_node)
            ):
                used_internally.add(name.str_rep)

        # Evaluate usage
        for member_node in members:
            member_name = member_node.enum_member_name

            loc_str = f"{member_node.rel_path}:{member_node.lineno}"

            if member_name.startswith("_"):
                if member_name not in used_internally:
                    unused_reports.append(
                        (
                            member_name,
                            class_name,
                            loc_str,
                            "Private member(s) internally not in use",
                        )
                    )
                continue

            if member_name in used_externally:
                continue

            if member_name in used_internally:
                unused_reports.append(
                    (
                        member_name,
                        class_name,
                        loc_str,
                        "Member(s) can be private",
                    )
                )
            else:
                unused_reports.append(
                    (
                        member_name,
                        class_name,
                        loc_str,
                        "Member(s) not accessed",
                    )
                )

    return sorted(unused_reports)


def test_enum_members(run_check: CheckRunner) -> None:
    run_check(get_unused)
