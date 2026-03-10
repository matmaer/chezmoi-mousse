import asyncio
from concurrent.futures import ThreadPoolExecutor

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


def _run_variant(combo: dict[str, bool]) -> None:

    async def _inner() -> None:
        test_app = ChezmoiGUI(**combo)
        async with test_app.run_test() as pilot:
            await pilot.pause()
            while isinstance(test_app.screen, SplashScreen):
                await pilot.pause(0.1)
            await pilot.pause()
            if combo["chezmoi_found"]:
                assert isinstance(test_app.screen, MainScreen)
            else:
                assert isinstance(test_app.screen, InstallHelpScreen)
            await pilot.press("ctrl+q")

    asyncio.run(_inner())


@pytest.mark.asyncio
async def test_app_starts_concurrently() -> None:
    # Each variant runs in its own thread with its own event loop so the apps
    # don't share a thread-pool executor and can't deadlock each other.
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=len(combos_to_test)) as pool:
        await asyncio.gather(
            *(loop.run_in_executor(pool, _run_variant, c) for c in combos_to_test)
        )
