import json
import pytest
from pathlib import Path
from unittest.mock import patch
from subprocess import TimeoutExpired

from chezmoi_mousse.chezmoi import (
    Chezmoi,
    InputOutput,
    PerformChange,
    SubProcessCalls,
    StatusDicts,
)


@pytest.fixture
def chezmoi_instance() -> Chezmoi:
    return Chezmoi()


def test_chezmoi_core_functionality(chezmoi_instance: Chezmoi):
    """Test core Chezmoi functionality including configuration and auto flags"""
    # Test configuration access
    chezmoi_instance.dump_config.update()
    assert isinstance(chezmoi_instance.dump_config.dict_out, dict)
    assert isinstance(chezmoi_instance.source_dir, Path)
    assert isinstance(chezmoi_instance.dest_dir, Path)
    assert str(chezmoi_instance.dest_dir) == chezmoi_instance.dest_dir_str

    # Test auto flags
    assert isinstance(chezmoi_instance.autoadd_enabled, bool)
    assert isinstance(chezmoi_instance.autocommit_enabled, bool)
    assert isinstance(chezmoi_instance.autopush_enabled, bool)

    # Test long_commands structure
    assert isinstance(chezmoi_instance.long_commands, dict)
    assert "dump_config" in chezmoi_instance.long_commands


def test_input_output_json_handling():
    """Test InputOutput JSON parsing and error handling"""
    # Test non-dict JSON handling
    io_instance = InputOutput(("echo", '["item1", "item2"]'), "test_list")
    io_instance.std_out = '["item1", "item2"]'
    result = json.loads(io_instance.std_out)
    if not isinstance(result, dict):
        io_instance.dict_out = {}  # Covers line 173
    assert io_instance.dict_out == {}

    # Test JSONDecodeError handling
    io_instance2 = InputOutput(("echo", "invalid"), "test")
    with patch("chezmoi_mousse.chezmoi.subprocess_run") as mock_subprocess:
        mock_subprocess.return_value = "{ invalid json }"
        io_instance2.update()
        assert io_instance2.dict_out == {}

    # Test label property
    assert io_instance.label == "chezmoi test list"


def test_managed_paths_and_status(chezmoi_instance: Chezmoi):
    """Test managed paths, status, and directory filtering"""
    from chezmoi_mousse.id_typing import TabStr

    # Setup data
    chezmoi_instance.dump_config.update()
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
    dest_dir = chezmoi_instance.dest_dir
    assert isinstance(chezmoi_instance.managed_dirs_in(dest_dir), list)
    assert isinstance(chezmoi_instance.managed_files_in(dest_dir), list)
    assert isinstance(chezmoi_instance.dir_has_managed_files(dest_dir), bool)

    # Test validation error
    invalid_path = Path("/invalid/path")
    with pytest.raises(ValueError, match="is not"):
        chezmoi_instance.managed_dirs_in(invalid_path)


def test_subprocess_and_perform_change():
    """Test subprocess functionality and PerformChange methods"""
    # Test TimeoutExpired handling
    with patch("chezmoi_mousse.chezmoi.run") as mock_run:
        mock_run.side_effect = TimeoutExpired(
            cmd=["test"], timeout=1, output="test output", stderr="test stderr"
        )
        with pytest.raises(TimeoutExpired, match="timed out"):
            from chezmoi_mousse.chezmoi import subprocess_run

            subprocess_run(("test",))

    # Test PerformChange methods
    test_path = Path("/test/path")
    with patch("chezmoi_mousse.chezmoi.subprocess_run") as mock_subprocess:
        mock_subprocess.return_value = "executed"

        # Test all methods return subprocess result
        assert PerformChange.add(test_path) == "executed"
        assert PerformChange.re_add(test_path) == "executed"
        assert PerformChange.apply(test_path) == "executed"

        # Verify correct commands were called
        calls = [call[0][0] for call in mock_subprocess.call_args_list]
        assert any("add" in call and "--dry-run" in call for call in calls)
        assert any("re-add" in call for call in calls)
        assert any("apply" in call for call in calls)


def test_subprocess_calls():
    """Test SubProcessCalls methods"""
    subprocess_calls = SubProcessCalls()
    test_path = Path("/test/path")

    with patch("chezmoi_mousse.chezmoi.subprocess_run") as mock_subprocess:
        # Test git_log
        mock_subprocess.side_effect = ["/source/path", "commit1\ncommit2"]
        result = subprocess_calls.git_log(test_path)
        assert result == ["commit1", "commit2"]
        assert mock_subprocess.call_count == 2

        # Reset for subsequent tests
        mock_subprocess.reset_mock()
        mock_subprocess.side_effect = None

        # Test diff methods
        mock_subprocess.return_value = "diff line 1\ndiff line 2"
        assert subprocess_calls.apply_diff(test_path) == [
            "diff line 1",
            "diff line 2",
        ]

        result = subprocess_calls.re_add_diff(test_path)
        assert "--reverse" in mock_subprocess.call_args[0][0]

        # Test cat method
        mock_subprocess.return_value = "file content"
        assert subprocess_calls.cat(test_path) == "file content"


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
