import ast

import pytest
from _test_utils import get_class_public_members, modules_to_test

from chezmoi_mousse.chezmoi import Chezmoi, ManagedStatus

exclude_files = ["chezmoi.py"]


@pytest.mark.parametrize(
    "member_name, member_type", get_class_public_members(Chezmoi)
)
def test_chezmoi_member_in_use(member_name: str, member_type: str):
    is_used = False

    for py_file in modules_to_test(exclude_file_names=exclude_files):
        content = py_file.read_text()
        tree = ast.parse(content, filename=str(py_file))

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == member_name:
                is_used = True
                break  # Found usage
        if is_used:
            break  # No need to check other files

    if not is_used:
        pytest.fail(f"\nNot in use: {member_name} {member_type}")


@pytest.mark.parametrize(
    "member_name, member_type", get_class_public_members(ManagedStatus)
)
def test_managed_status_member_in_use(member_name: str, member_type: str):
    is_used = False

    # Exclude chezmoi.py from the search
    for py_file in modules_to_test(exclude_file_names=exclude_files):
        content = py_file.read_text()
        tree = ast.parse(content, filename=str(py_file))

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == member_name:
                is_used = True

        if is_used:
            break  # Found usage, no need to check other files

    if not is_used:
        pytest.fail(f"\nNot in use: {member_name} {member_type}")
