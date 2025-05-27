import pytest

from chezmoi_mousse.gui import ChezmoiTUI


def test_chezmoi_tui_instantiation():
    try:
        ChezmoiTUI()
    except Exception as e:
        pytest.fail(f"MainScreen instantiation failed with exception: {e}")
