import pytest

import chezmoi_mousse.main_tabs as main_tabs


@pytest.fixture
def dummy_path(tmp_path):
    file = tmp_path / "dummy.txt"
    file.write_text("test")
    return file


def test_add_tab_instantiation():
    tab = main_tabs.AddTab()
    assert isinstance(tab, main_tabs.AddTab)


def test_git_log_instantiation():
    modal = main_tabs.GitLog()
    assert isinstance(modal, main_tabs.GitLog)


def test_doctor_tab_instantiation():
    tab = main_tabs.DoctorTab()
    assert isinstance(tab, main_tabs.DoctorTab)


def test_diagram_tab_instantiation():
    tab = main_tabs.DiagramTab()
    assert isinstance(tab, main_tabs.DiagramTab)
