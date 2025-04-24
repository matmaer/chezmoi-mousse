from pathlib import Path

import pytest

from chezmoi_mousse.chezmoi import Chezmoi


@pytest.fixture
def chezmoi_instance():
    return Chezmoi()


def test_chezmoi_instantiation():
    try:
        instance = Chezmoi()
    except Exception as e:
        pytest.fail(f"Chezmoi instantiation failed with exception: {e}")


def test_dump_config(chezmoi_instance):
    chezmoi_instance.dump_config.update()
    assert isinstance(chezmoi_instance.dump_config.dict_out, dict)


def test_template_data(chezmoi_instance):
    chezmoi_instance.template_data.update()
    assert isinstance(chezmoi_instance.template_data.dict_out, dict)


def test_doctor(chezmoi_instance):
    chezmoi_instance.doctor.update()
    assert isinstance(chezmoi_instance.doctor.list_out, list)


def test_cat_config(chezmoi_instance):
    chezmoi_instance.cat_config.update()
    assert isinstance(chezmoi_instance.cat_config.list_out, list)


def test_git_log(chezmoi_instance):
    chezmoi_instance.git_log.update()
    assert isinstance(chezmoi_instance.git_log.list_out, list)


def test_ignored(chezmoi_instance):
    chezmoi_instance.ignored.update()
    assert isinstance(chezmoi_instance.ignored.list_out, list)


def test_managed_files(chezmoi_instance):
    chezmoi_instance.managed_files.update()
    assert isinstance(chezmoi_instance.managed_files.list_out, list)


def test_managed_dirs(chezmoi_instance):
    chezmoi_instance.managed_dirs.update()
    assert isinstance(chezmoi_instance.managed_dirs.list_out, list)


def test_status_files(chezmoi_instance):
    chezmoi_instance.status_files.update()
    assert isinstance(chezmoi_instance.status_files.list_out, list)


def test_status_dirs(chezmoi_instance):
    chezmoi_instance.status_dirs.update()
    assert isinstance(chezmoi_instance.status_dirs.list_out, list)


def test_unmanaged_in_d_invalid_dir(chezmoi_instance):
    with pytest.raises(ValueError):
        chezmoi_instance.unmanaged_in_d(Path("/invalid/path"))
