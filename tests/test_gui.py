import pytest
from chezmoi_mousse.gui import ChezmoiTUI, MainScreen, LoadingScreen


def test_chezmoi_tui_instantiation():
    try:
        instance = ChezmoiTUI()
    except Exception as e:
        pytest.fail(f"MainScreen instantiation failed with exception: {e}")


def test_loading_screen_instantiation():
    try:
        instance = LoadingScreen()
    except Exception as e:
        pytest.fail(f"MainScreen instantiation failed with exception: {e}")


def test_main_screen_instantiation():
    try:
        instance = MainScreen()
    except Exception as e:
        pytest.fail(f"MainScreen instantiation failed with exception: {e}")
