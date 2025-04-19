from chezmoi_mousse.gui import MainScreen
import pytest


def test_main_screen_instantiation():
    try:
        instance = MainScreen()
    except Exception as e:
        pytest.fail(f"MainScreen instantiation failed with exception: {e}")
