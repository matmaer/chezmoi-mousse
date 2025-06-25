import pytest

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
