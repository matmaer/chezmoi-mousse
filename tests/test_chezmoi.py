from pathlib import Path

import pytest

from chezmoi_mousse import components
from chezmoi_mousse.chezmoi import Chezmoi


@pytest.fixture
def chezmoi_instance():
    return Chezmoi()


def test_chezmoi_instantiation():
    instance = Chezmoi()
    assert isinstance(instance, Chezmoi)


def test_has_expected_attributes(chezmoi_instance):
    # Check that main attributes exist
    for attr in [
        "dump_config",
        "template_data",
        "doctor",
        "cat_config",
        "git_log",
        "ignored",
        "managed_files",
        "managed_dirs",
        "status_files",
    ]:
        assert hasattr(chezmoi_instance, attr)


def test_update_methods_exist(chezmoi_instance):
    # Check that update methods exist for main attributes
    for attr in [
        "dump_config",
        "template_data",
        "doctor",
        "cat_config",
        "git_log",
        "ignored",
        "managed_files",
        "managed_dirs",
        "status_files",
    ]:
        obj = getattr(chezmoi_instance, attr)
        assert hasattr(obj, "update") and callable(obj.update)


def test_update_and_output_types(chezmoi_instance):
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


def test_status_files_update(chezmoi_instance):
    # Just ensure update does not raise
    chezmoi_instance.status_files.update()


def test_auto_flags(chezmoi_instance):
    chezmoi_instance.dump_config.update()
    assert isinstance(chezmoi_instance.autoadd_enabled, bool)
    assert isinstance(chezmoi_instance.autocommit_enabled, bool)
    assert isinstance(chezmoi_instance.autopush_enabled, bool)


# --- Components.py coverage ---


def test_staticdiff_instantiation(monkeypatch, tmp_path):
    file = tmp_path / "file.txt"
    file.write_text("foo")
    monkeypatch.setattr(
        components.chezmoi,
        "diff",
        lambda path, apply: ["+added", "-removed", " unchanged"],
    )
    sd = components.StaticDiff(file, apply=True)
    assert isinstance(sd, components.StaticDiff)
    sd.on_mount()


def test_filtereddirtree_instantiation(monkeypatch, tmp_path):
    tree = components.FilteredDirTree(tmp_path)
    assert isinstance(tree, components.FilteredDirTree)


def test_chezmoistatus_instantiation():
    cs = components.ChezmoiStatus(apply=True)
    assert isinstance(cs, components.ChezmoiStatus)


def test_filterbar_instantiation():
    fb = components.FilterBar(filter_key="main", tab_filters_id="tab1")
    assert isinstance(fb, components.FilterBar)
