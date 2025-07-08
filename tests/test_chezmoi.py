from pathlib import Path

import pytest

from chezmoi_mousse.chezmoi import Chezmoi, StatusDicts

from chezmoi_mousse import CM_CFG


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
    assert isinstance(chezmoi_instance.managed_files_in(dest_dir), list)
    assert isinstance(chezmoi_instance.dir_has_managed_files(dest_dir), bool)

    # Test validation error
    invalid_path = Path("/invalid/path")
    with pytest.raises(ValueError, match="is not"):
        chezmoi_instance.managed_dirs_in(invalid_path)


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
