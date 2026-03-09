import time

from chezmoi_mousse.gui.install_help import InstallHelpScreen
from chezmoi_mousse.gui.main_screen import MainScreen
from chezmoi_mousse.gui.splash_screen import SplashScreen
from chezmoi_mousse.gui.textual_app import ChezmoiGUI


async def test_main_screen_renders() -> None:
    test_app = ChezmoiGUI(chezmoi_found=True, dev_mode=False, pretend_init_needed=False)

    async with test_app.run_test() as pilot:
        await pilot.pause()  # Allow SplashScreen to render
        start_time = time.time()
        while isinstance(test_app.screen, SplashScreen):
            if time.time() - start_time > 2:
                raise TimeoutError("SplashScreen did not dismiss within 2 seconds")
            await pilot.pause(0.1)
        await pilot.pause()  # Allow MainScreen to render
        assert isinstance(test_app.screen, MainScreen)
        await pilot.press("ctrl+q")


async def test_main_screen_renders_dev_mode() -> None:
    test_app = ChezmoiGUI(chezmoi_found=True, dev_mode=True, pretend_init_needed=False)

    async with test_app.run_test() as pilot:
        await pilot.pause()  # Allow SplashScreen to render
        start_time = time.time()
        while isinstance(test_app.screen, SplashScreen):
            if time.time() - start_time > 2:
                raise TimeoutError("SplashScreen did not dismiss within 2 seconds")
            await pilot.pause(0.1)
        await pilot.pause()  # Allow MainScreen to render
        assert isinstance(test_app.screen, MainScreen)
        await pilot.press("ctrl+q")


async def test_install_help_screen_renders() -> None:
    test_app = ChezmoiGUI(
        chezmoi_found=False, dev_mode=False, pretend_init_needed=False
    )

    async with test_app.run_test() as pilot:
        await pilot.pause()  # Allow SplashScreen to render
        start_time = time.time()
        while isinstance(test_app.screen, SplashScreen):
            if time.time() - start_time > 1.5:
                raise TimeoutError("SplashScreen did not dismiss within 1.5 seconds")
            await pilot.pause(0.1)
        await pilot.pause()  # Allow InstallHelpScreen to render
        assert isinstance(test_app.screen, InstallHelpScreen)
        await pilot.press("ctrl+q")


async def test_install_help_screen_renders_dev_mode() -> None:
    test_app = ChezmoiGUI(chezmoi_found=False, dev_mode=True, pretend_init_needed=False)

    async with test_app.run_test() as pilot:
        await pilot.pause()  # Allow SplashScreen to render
        start_time = time.time()
        while isinstance(test_app.screen, SplashScreen):
            if time.time() - start_time > 1.5:
                raise TimeoutError("SplashScreen did not dismiss within 1.5 seconds")
            await pilot.pause(0.1)
        await pilot.pause()  # Allow InstallHelpScreen to render
        assert isinstance(test_app.screen, InstallHelpScreen)
        await pilot.press("ctrl+q")
