import pytest

from chezmoi_mousse.splash_screen import AnimatedFade, LoadingScreen


def test_loading_screen_instantiation():
    try:
        instance = LoadingScreen()
    except Exception as e:
        pytest.fail(f"ChezmoiStatus instantiation failed with exception: {e}")


def test_animated_fade_instantiation():
    try:
        instance = AnimatedFade()
    except Exception as e:
        pytest.fail(f"ChezmoiStatus instantiation failed with exception: {e}")
