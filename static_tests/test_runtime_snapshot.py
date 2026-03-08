from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from textual.pilot import Pilot

from chezmoi_mousse import IDS, TabLabel
from chezmoi_mousse.gui.textual_app import ChezmoiGUI

SNAPSHOT_CSS_PATH = str(
    Path(__file__).resolve().parents[1] / "src/chezmoi_mousse/gui/gui.tcss"
)


class SnapshotChezmoiGUI(ChezmoiGUI):
    CSS_PATH = SNAPSHOT_CSS_PATH


def _open_main_screen_immediately(self: ChezmoiGUI) -> None:
    from chezmoi_mousse.gui.main_screen import MainScreen

    self.push_screen(MainScreen())


def _new_snapshot_app() -> ChezmoiGUI:
    app = SnapshotChezmoiGUI(
        chezmoi_found=True, dev_mode=False, pretend_init_needed=False
    )
    return app


def test_main_screen_snapshot(
    snap_compare: Callable[..., bool], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ChezmoiGUI, "_run_splash_screen", _open_main_screen_immediately)
    app = _new_snapshot_app()
    assert snap_compare(app, terminal_size=(120, 40))


def test_apply_contents_view_snapshot(
    snap_compare: Callable[..., bool], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ChezmoiGUI, "_run_splash_screen", _open_main_screen_immediately)

    async def run_before(pilot: Pilot[Any]) -> None:
        await pilot.pause()
        await pilot.click(f"#{IDS.apply.tab_button_id(btn=TabLabel.contents)}")
        await pilot.pause()

    app = _new_snapshot_app()
    assert snap_compare(app, terminal_size=(120, 40), run_before=run_before)
