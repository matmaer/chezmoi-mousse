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


def test_doctor_tab_instantiation():
    tab = main_tabs.DoctorTab()
    assert isinstance(tab, main_tabs.DoctorTab)
