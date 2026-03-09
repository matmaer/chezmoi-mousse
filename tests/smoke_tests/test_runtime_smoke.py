import asyncio
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


@pytest.mark.asyncio
async def test_app_starts_concurrently() -> None:
    async def run_single_variant(combo: dict[str, bool]) -> None:
        test_app = ChezmoiGUI(**combo)
        async with test_app.run_test() as pilot:
            await pilot.pause()  # Allow SplashScreen to render
            start_time = time.monotonic()
            while isinstance(test_app.screen, SplashScreen):
                if time.monotonic() - start_time > 2.1:
                    raise TimeoutError(
                        f"SplashScreen for {combo} took more than 2.1s to dismiss."
                    )
                await pilot.pause(0.1)
            await pilot.pause()  # Allow next screen to render

            if combo["chezmoi_found"]:
                assert isinstance(test_app.screen, MainScreen)
            else:
                assert isinstance(test_app.screen, InstallHelpScreen)
            await pilot.press("ctrl+q")

    # Run all variants in parallel using asyncio.gather
    await asyncio.gather(*(run_single_variant(c) for c in combos_to_test))
