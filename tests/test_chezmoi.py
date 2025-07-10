from pathlib import Path

import pytest

from chezmoi_mousse import CM_CFG
from chezmoi_mousse.chezmoi import Chezmoi, StatusDicts


@pytest.fixture
def chezmoi_instance() -> Chezmoi:
    return Chezmoi()


def test_managed_paths_and_status(chezmoi_instance: Chezmoi):
    """Test managed paths and status"""
    from chezmoi_mousse.id_typing import TabStr

    # Setup data
    chezmoi_instance.managed_dirs.update()
    chezmoi_instance.managed_files.update()
    chezmoi_instance.dir_status_lines.update()
    chezmoi_instance.file_status_lines.update()

    # Test managed paths
    assert isinstance(chezmoi_instance.managed_dir_paths, list)
    assert isinstance(chezmoi_instance.managed_file_paths, list)

    # Test status structure
    status = chezmoi_instance.managed_status
    assert isinstance(status, dict)
    assert TabStr.apply_tab in status and TabStr.re_add_tab in status

    # Test directory filtering with dest_dir
    dest_dir = CM_CFG.destDir
    assert isinstance(chezmoi_instance.managed_dirs_in(dest_dir), list)


def test_status_dicts_properties():
    """Test StatusDicts filtering properties"""
    test_dirs = {
        Path("/test/dir1"): "X",
        Path("/test/dir2"): "M",
        Path("/test/dir3"): "A",
        Path("/test/dir4"): "X",
    }
    test_files = {
        Path("/test/file1.txt"): "X",
        Path("/test/file2.txt"): "M",
        Path("/test/file3.txt"): "D",
        Path("/test/file4.txt"): "X",
    }

    status_dicts = StatusDicts(dirs=test_dirs, files=test_files)

    # Test filtering properties
    assert len(status_dicts.dirs_without_status) == 2  # X status items
    assert len(status_dicts.files_without_status) == 2  # X status items
    assert len(status_dicts.dirs_with_status) == 2  # M, A status items
    assert len(status_dicts.files_with_status) == 2  # M, D status items


def _get_chezmoi_public_members() -> list[tuple[str, str]]:
    import inspect

    members: list[tuple[str, str]] = []
    for name, member in inspect.getmembers(Chezmoi):
        if not name.startswith("_"):
            if isinstance(member, property):
                members.append((name, "property"))
            elif inspect.isfunction(member):
                members.append((name, "method"))
    return members


@pytest.mark.parametrize(
    "member_name, member_type", _get_chezmoi_public_members()
)
def test_member_in_use(member_name: str, member_type: str):
    import ast

    from _test_utils import modules_to_test

    is_used = False
    usage_locations: list[str] = []

    # Exclude chezmoi.py from the search
    for py_file in modules_to_test(exclude_file_names=["chezmoi.py"]):
        content = py_file.read_text()
        tree = ast.parse(content, filename=str(py_file))

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == member_name:
                is_used = True
                usage_locations.append(f"{py_file.name}:{node.lineno}")

        if is_used:
            break  # Found usage, no need to check other files

    if not is_used:
        pytest.skip(
            f"Unused Chezmoi {member_type}: '{member_name}' is not used in the codebase.\n"
            "If this is intentional for internal use, consider renaming it with a leading underscore."
        )
