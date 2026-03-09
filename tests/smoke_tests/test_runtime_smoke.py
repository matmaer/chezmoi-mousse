import pytest
from textual.widgets import ContentSwitcher, TabbedContent

from chezmoi_mousse import IDS, TabLabel
from chezmoi_mousse.gui.common.switchers import ViewSwitcher
from chezmoi_mousse.gui.main_screen import MainScreen
from chezmoi_mousse.gui.textual_app import ChezmoiGUI


def _open_main_screen_immediately(self: ChezmoiGUI) -> None:
    # Bypass SplashScreen for now
    self.push_screen(MainScreen())


async def test_app_starts_and_main_screen_renders(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Smoke test app startup in headless mode
    monkeypatch.setattr(ChezmoiGUI, "_run_splash_screen", _open_main_screen_immediately)
    app = ChezmoiGUI(chezmoi_found=True, dev_mode=False, pretend_init_needed=False)

    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, MainScreen)
        tabbed_content = app.screen.query_exactly_one(TabbedContent)
        assert tabbed_content.active == TabLabel.apply


async def test_apply_view_switcher_tab_buttons(monkeypatch: pytest.MonkeyPatch) -> None:
    # Smoke test clicking Diff/Contents/Git-Log view buttons in Apply tab
    monkeypatch.setattr(ChezmoiGUI, "_run_splash_screen", _open_main_screen_immediately)
    app = ChezmoiGUI(chezmoi_found=True, dev_mode=False, pretend_init_needed=False)

    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        # Click Contents button and verify switched view.
        await pilot.click(f"#{IDS.apply.tab_button_id(btn=TabLabel.contents)}")
        await pilot.pause()
        view_switcher = app.screen.query_one(
            IDS.apply.container.right_side_q, ViewSwitcher
        )
        content_switcher = view_switcher.query_exactly_one(ContentSwitcher)
        assert content_switcher.current == IDS.apply.container.contents

        # Click Git-Log button and verify switched view.
        await pilot.click(f"#{IDS.apply.tab_button_id(btn=TabLabel.git_log)}")
        await pilot.pause()
        assert content_switcher.current == IDS.apply.container.git_log

        # Click Diff button and verify switched view.
        await pilot.click(f"#{IDS.apply.tab_button_id(btn=TabLabel.diff)}")
        await pilot.pause()
        assert content_switcher.current == IDS.apply.container.diff


async def test_common_key_actions_do_not_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    # Smoke test a couple of global key actions wired in ChezmoiGUI
    monkeypatch.setattr(ChezmoiGUI, "_run_splash_screen", _open_main_screen_immediately)
    app = ChezmoiGUI(chezmoi_found=True, dev_mode=False, pretend_init_needed=False)

    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.press("f")
        await pilot.pause()
        await pilot.press("f")
        await pilot.pause()
        await pilot.press("m")
        await pilot.pause()
        await pilot.press("m")
        await pilot.pause()
