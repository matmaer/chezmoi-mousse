import ast
from pathlib import Path

import pytest
from _test_utils import get_modules_importing_class

from chezmoi_mousse import Id, TabIds


def _get_class_public_members_strings(
    class_object: type,
) -> list[tuple[str, str]]:
    members: list[tuple[str, str]] = []
    for name in dir(class_object):
        if not name.startswith("_"):
            attr = getattr(class_object, name)
            if isinstance(attr, property):
                members.append((name, "property"))
            elif callable(attr):  # This catches all callable types
                members.append((name, "method"))
            else:
                members.append((name, "attribute"))
    return members


class UsageFinder(ast.NodeVisitor):
    def __init__(self, member_name: str, exclude_class_name: str):
        self.member_name = member_name
        self.exclude_class_name = exclude_class_name
        self.found = False

    def visit_Attribute(self, node: ast.Attribute):
        if node.attr == self.member_name:
            self.found = True
        self.generic_visit(node)  # recurse into nested attributes

    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if (
                isinstance(target, ast.Attribute)
                and target.attr == self.member_name
            ):
                self.found = True
        self.generic_visit(node)  # recurse into nested attributes

    def visit_ClassDef(self, node: ast.ClassDef):
        if node.name == self.exclude_class_name:
            # Visit the __init__ method to check for usage there
            for item in node.body:
                if (
                    isinstance(item, ast.FunctionDef)
                    and item.name == "__init__"
                ):
                    self.visit(item)
        else:
            self.generic_visit(node)


@pytest.mark.parametrize(
    "member_name, member_type",
    _get_class_public_members_strings(TabIds),
    ids=[name for name, _ in _get_class_public_members_strings(TabIds)],
)
def test_tabids_member_in_use(member_name: str, member_type: str):
    is_used = False
    class_name = "TabIds"

    # the test should run on all modules importing TabIds and the Id class as
    # the TabIds members can be accessed via an Id attribute
    paths_to_check: set[Path] = set(
        get_modules_importing_class(class_name)
        + get_modules_importing_class("Id")
    )
    for py_file in paths_to_check:
        content = py_file.read_text()
        tree = ast.parse(content, filename=str(py_file))

        finder = UsageFinder(member_name, exclude_class_name=class_name)
        finder.visit(tree)
        if finder.found:
            is_used = True
            break  # No need to check other files

    if not is_used:
        pytest.fail(f"\nNot in use: {member_name} {member_type}")


@pytest.mark.parametrize(
    "member_name, member_type",
    _get_class_public_members_strings(Id),
    ids=[name for name, _ in _get_class_public_members_strings(Id)],
)
def test_id_members_in_use(member_name: str, member_type: str):
    is_used = False
    class_name = "Id"

    for py_file in get_modules_importing_class(class_name):
        content = py_file.read_text()
        tree = ast.parse(content, filename=str(py_file))

        finder = UsageFinder(member_name, exclude_class_name=class_name)
        finder.visit(tree)
        if finder.found:
            is_used = True
            break  # No need to check other files

    if not is_used:
        pytest.fail(f"\nNot in use: {member_name} {member_type}")
