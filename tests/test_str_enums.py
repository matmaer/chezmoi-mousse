"""Test if all members from the StrEnum classes in enums.py are in use"""

import ast
from pathlib import Path

import pytest
from _test_utils import get_module_ast_tree, get_module_paths


class UsageFinder(ast.NodeVisitor):
    def __init__(self, class_name: str):
        self.class_name = class_name
        self.usages: set[str] = set()

    def visit_Attribute(self, node: ast.Attribute):
        # Check if this is an attribute access on the target class (e.g., Tcss.some_member or Chars.some_member)
        if (
            isinstance(node.value, ast.Name)
            and node.value.id == self.class_name
        ):
            self.usages.add(node.attr)


def get_str_enum_assign_members(class_def: ast.ClassDef) -> list[ast.Assign]:
    members: list[ast.Assign] = []
    for node in class_def.body:
        if isinstance(node, ast.Assign):
            # Assuming all top-level assignments in an Enum class are members
            members.append(node)
    return members


def get_id_typing_str_enum_class_defs() -> list[ast.ClassDef]:
    str_enum_file = Path("src/chezmoi_mousse/id_typing/_str_enums.py")
    tree = ast.parse(str_enum_file.read_text())
    class_defs: list[ast.ClassDef] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_defs.append(node)
    return class_defs


@pytest.mark.parametrize(
    "str_enum_class_def",
    get_id_typing_str_enum_class_defs(),
    ids=lambda str_enum_class_def: str_enum_class_def.name,
)
def test_members_in_use(str_enum_class_def: ast.ClassDef):
    # Get all member names for this class
    members = get_str_enum_assign_members(str_enum_class_def)
    member_names = [
        m.targets[0].id for m in members if isinstance(m.targets[0], ast.Name)
    ]

    # Collect all usages of this class's attributes across all modules
    usages: set[str] = set()
    for module_path in get_module_paths(
        exclude_paths=[Path("id_typing", "_str_enums.py")]
    ):
        tree = get_module_ast_tree(module_path)
        finder = UsageFinder(str_enum_class_def.name)
        finder.visit(tree)
        usages.update(finder.usages)

    # Check each member is used
    for member_name in member_names:
        assert (
            member_name in usages
        ), f"Member {str_enum_class_def.name}.{member_name} is not used in any module."
