import pytest
from pathlib import Path

from chezmoi_mousse.chezmoi import Chezmoi


@pytest.fixture
def chezmoi_instance() -> Chezmoi:
    return Chezmoi()


def test_chezmoi_instantiation():
    instance: Chezmoi = Chezmoi()
    assert isinstance(instance, Chezmoi)


def test_update_and_output_types(chezmoi_instance: Chezmoi):

    # Call update and check output types for main attributes
    chezmoi_instance.dump_config.update()
    assert isinstance(chezmoi_instance.dump_config.dict_out, dict)

    chezmoi_instance.template_data.update()
    assert isinstance(chezmoi_instance.template_data.dict_out, dict)

    chezmoi_instance.doctor.update()
    assert isinstance(chezmoi_instance.doctor.list_out, list)

    chezmoi_instance.cat_config.update()
    assert isinstance(chezmoi_instance.cat_config.list_out, list)

    chezmoi_instance.git_log.update()
    assert isinstance(chezmoi_instance.git_log.list_out, list)

    chezmoi_instance.ignored.update()
    assert isinstance(chezmoi_instance.ignored.list_out, list)

    chezmoi_instance.managed_files.update()
    assert isinstance(chezmoi_instance.managed_files.list_out, list)

    chezmoi_instance.managed_dirs.update()
    assert isinstance(chezmoi_instance.managed_dirs.list_out, list)


def test_auto_flags(chezmoi_instance: Chezmoi):
    chezmoi_instance.dump_config.update()
    assert isinstance(chezmoi_instance.autoadd_enabled, bool)
    assert isinstance(chezmoi_instance.autocommit_enabled, bool)
    assert isinstance(chezmoi_instance.autopush_enabled, bool)


def test_managed_dir_paths_type(chezmoi_instance: Chezmoi):
    chezmoi_instance.managed_dirs.update()
    paths = chezmoi_instance.managed_dir_paths
    assert isinstance(paths, list)
    for p in paths:
        assert hasattr(p, "exists")  # Path object


def test_managed_file_paths_type(chezmoi_instance: Chezmoi):
    chezmoi_instance.managed_files.update()
    paths = chezmoi_instance.managed_file_paths
    assert isinstance(paths, list)
    for p in paths:
        assert hasattr(p, "exists")  # Path object


def test_perform_add_and_apply_methods_exist(chezmoi_instance: Chezmoi):
    assert hasattr(chezmoi_instance.perform, "add")
    assert hasattr(chezmoi_instance.perform, "apply")
    assert callable(chezmoi_instance.perform.add)
    assert callable(chezmoi_instance.perform.apply)


def test_run_git_log_and_cat_methods_exist(chezmoi_instance: Chezmoi):
    assert hasattr(chezmoi_instance.run, "git_log")
    assert hasattr(chezmoi_instance.run, "cat")
    assert callable(chezmoi_instance.run.git_log)
    assert callable(chezmoi_instance.run.cat)


def test_source_and_dest_dirs(chezmoi_instance: Chezmoi):
    """Test source_dir, dest_dir, and dest_dir_str properties"""
    chezmoi_instance.dump_config.update()
    assert isinstance(chezmoi_instance.source_dir, Path)
    assert isinstance(chezmoi_instance.dest_dir, Path)
    assert isinstance(chezmoi_instance.dest_dir_str, str)
    assert str(chezmoi_instance.dest_dir) == chezmoi_instance.dest_dir_str


def test_input_output_label_property(chezmoi_instance: Chezmoi):
    """Test InputOutput label property"""
    assert chezmoi_instance.dump_config.label == "chezmoi dump config"
    assert chezmoi_instance.cat_config.label == "chezmoi cat config"
    assert chezmoi_instance.git_log.label == "chezmoi git log"


def test_status_lines_attributes(chezmoi_instance: Chezmoi):
    """Test status lines attributes exist and are InputOutput instances"""
    assert hasattr(chezmoi_instance, "dir_status_lines")
    assert hasattr(chezmoi_instance, "file_status_lines")
    assert hasattr(chezmoi_instance.dir_status_lines, "update")
    assert hasattr(chezmoi_instance.file_status_lines, "update")


def test_managed_source_attributes(chezmoi_instance: Chezmoi):
    """Test managed source path attributes"""
    assert hasattr(chezmoi_instance, "managed_dirs_source")
    assert hasattr(chezmoi_instance, "managed_files_source")
    assert hasattr(chezmoi_instance.managed_dirs_source, "update")
    assert hasattr(chezmoi_instance.managed_files_source, "update")


def test_perform_re_add_method_exists(chezmoi_instance: Chezmoi):
    """Test re_add method exists in PerformChange"""
    assert hasattr(chezmoi_instance.perform, "re_add")
    assert callable(chezmoi_instance.perform.re_add)


def test_run_diff_methods_exist(chezmoi_instance: Chezmoi):
    """Test diff methods exist in SubProcessCalls"""
    assert hasattr(chezmoi_instance.run, "apply_diff")
    assert hasattr(chezmoi_instance.run, "re_add_diff")
    assert callable(chezmoi_instance.run.apply_diff)
    assert callable(chezmoi_instance.run.re_add_diff)


def test_managed_status_property_structure(chezmoi_instance: Chezmoi):
    """Test managed_status property returns correct structure"""
    from chezmoi_mousse.id_typing import TabStr

    # Setup required data first
    chezmoi_instance.dump_config.update()
    chezmoi_instance.managed_dirs.update()
    chezmoi_instance.managed_files.update()
    chezmoi_instance.dir_status_lines.update()
    chezmoi_instance.file_status_lines.update()

    status = chezmoi_instance.managed_status
    assert isinstance(status, dict)
    assert TabStr.apply_tab in status
    assert TabStr.re_add_tab in status

    # Check StatusDicts structure
    for tab_status in status.values():
        assert hasattr(tab_status, "dirs")
        assert hasattr(tab_status, "files")
        assert hasattr(tab_status, "dirs_with_status")
        assert hasattr(tab_status, "files_with_status")
        assert hasattr(tab_status, "dirs_without_status")
        assert hasattr(tab_status, "files_without_status")


def test_validation_methods_exist(chezmoi_instance: Chezmoi):
    """Test directory validation and filtering methods exist"""
    assert hasattr(chezmoi_instance, "managed_dirs_in")
    assert hasattr(chezmoi_instance, "managed_files_in")
    assert hasattr(chezmoi_instance, "dirs_with_status_in")
    assert hasattr(chezmoi_instance, "files_with_status_in")
    assert hasattr(chezmoi_instance, "dirs_without_status_in")
    assert hasattr(chezmoi_instance, "files_without_status_in")
    assert hasattr(chezmoi_instance, "dir_has_managed_files")
    assert hasattr(chezmoi_instance, "dir_has_status_files")
    assert hasattr(chezmoi_instance, "dir_has_status_dirs")

    # Check they are callable
    assert callable(chezmoi_instance.managed_dirs_in)
    assert callable(chezmoi_instance.managed_files_in)
    assert callable(chezmoi_instance.dir_has_managed_files)


def test_long_commands_dict(chezmoi_instance: Chezmoi):
    """Test long_commands dictionary is populated"""
    assert hasattr(chezmoi_instance, "long_commands")
    assert isinstance(chezmoi_instance.long_commands, dict)
    assert len(chezmoi_instance.long_commands) > 0

    # Check some expected commands exist
    expected_commands = [
        "dump_config",
        "cat_config",
        "doctor",
        "managed_files",
        "managed_dirs",
    ]
    for cmd in expected_commands:
        assert cmd in chezmoi_instance.long_commands
        assert isinstance(chezmoi_instance.long_commands[cmd], tuple)
