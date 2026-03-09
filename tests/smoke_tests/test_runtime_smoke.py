import time

import pytest

from chezmoi_mousse.gui.install_help import InstallHelpScreen
from chezmoi_mousse.gui.main_screen import MainScreen
from chezmoi_mousse.gui.splash_screen import SplashScreen
from chezmoi_mousse.gui.textual_app import ChezmoiGUI

combos_to_test: list[dict[str, bool]] = [
    {"chezmoi_found": True, "dev_mode": True, "pretend_init_needed": False},
    {"chezmoi_found": True, "dev_mode": False, "pretend_init_needed": False},
    {"chezmoi_found": False, "dev_mode": True, "pretend_init_needed": False},
    {"chezmoi_found": False, "dev_mode": False, "pretend_init_needed": False},
]


@pytest.mark.parametrize("combo", combos_to_test, ids=lambda c: f"{c}")
async def test_app_starts(combo: dict[str, bool]) -> None:
    test_app = ChezmoiGUI(**combo)
    async with test_app.run_test() as pilot:
        await pilot.pause()  # Allow SplashScreen to render
        start_time = time.time()
        while isinstance(test_app.screen, SplashScreen):
            if time.time() - start_time > 2:
                raise TimeoutError("SplashScreen did not dismiss within 2 seconds")
            await pilot.pause(0.1)
        await pilot.pause()  # Allow next screen to render

        if combo["chezmoi_found"]:
            assert isinstance(test_app.screen, MainScreen)
        else:
            assert isinstance(test_app.screen, InstallHelpScreen)
        await pilot.press("ctrl+q")
