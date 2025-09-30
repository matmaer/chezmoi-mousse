import ast

import pytest
from _test_utils import get_class_public_members_strings, get_module_paths

from chezmoi_mousse.chezmoi import Chezmoi

exclude_files = ["chezmoi.py"]


@pytest.mark.parametrize(
    "member_name, member_type", get_class_public_members_strings(Chezmoi)
)
def test_member_in_use(member_name: str, member_type: str):
    is_used = False

    for py_file in get_module_paths(exclude_file_names=exclude_files):
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
