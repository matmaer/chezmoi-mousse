"""Module for testing the application by interfacing programmatically.

This is work in progress.
Source for the Pilot class is here: textual/pilot.py
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from textual.widgets import Button

from ._str_enums import TabLabel

if TYPE_CHECKING:
    from .gui.textual_app import ChezmoiGUI


async def test_app_with_pilot(app: ChezmoiGUI):
    async with app.run_test(headless=False, notifications=True) as pilot:
        await pilot.pause(5)
        # random POC test
        buttons: Iterator[Button] = pilot.app.screen.query(Button).results()
        tab_buttons: list[str] = [f"{b.label}" for b in buttons if b.label in TabLabel]
        pilot.app.notify(f"Found tab buttons: {tab_buttons}")
        await pilot.pause(5)
        await pilot.exit(None)
