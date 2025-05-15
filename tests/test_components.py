from pathlib import Path

import pytest

import chezmoi_mousse.mousse as mousse


@pytest.fixture
def dummy_path(tmp_path):
    file = tmp_path / "dummy.txt"
    file.write_text("test")
    return file


def test_add_tab_instantiation():
    tab = mousse.AddTab()
    assert isinstance(tab, mousse.AddTab)


def test_chezmoi_add_instantiation(dummy_path):
    modal = mousse.ChezmoiAdd(dummy_path)
    assert isinstance(modal, mousse.ChezmoiAdd)


def test_git_log_instantiation():
    modal = mousse.GitLog()
    assert isinstance(modal, mousse.GitLog)


def test_config_dump_instantiation():
    modal = mousse.ConfigDump()
    assert isinstance(modal, mousse.ConfigDump)


def test_doctor_tab_instantiation():
    tab = mousse.DoctorTab()
    assert isinstance(tab, mousse.DoctorTab)


def test_apply_tab_instantiation():
    tab = mousse.ApplyTab()
    assert isinstance(tab, mousse.ApplyTab)


def test_re_add_tab_instantiation():
    tab = mousse.ReAddTab()
    assert isinstance(tab, mousse.ReAddTab)


def test_diagram_tab_instantiation():
    tab = mousse.DiagramTab()
    assert isinstance(tab, mousse.DiagramTab)
