"""Module for testing the application by interfacing programmatically.

This is work in progress.
Source for the Pilot class is here: textual/pilot.py
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from textual.pilot import Pilot
from textual.widgets import TabbedContent

from ._str_enums import TabLabel

if TYPE_CHECKING:
    from .gui.textual_app import ChezmoiGUI


class PMTimeOut(Enum):
    min_pause = 0.1
    start_stop = 5.0


async def pilot_chill(pilot: Pilot[None]):
    await pilot.wait_for_scheduled_animations()
    await pilot.pause(PMTimeOut.min_pause.value)


async def test_binding(pilot: Pilot[None], key: str):
    await pilot.press(key)
    await pilot_chill(pilot)
    await pilot.press(key)
    await pilot_chill(pilot)


async def click_tab(
    pilot: Pilot[None], label: TabLabel, tabbed_content: TabbedContent
) -> None:
    tab = tabbed_content.get_tab(label)
    await pilot.click(tab)
    await pilot_chill(pilot)


async def test_app_with_pilot(app: ChezmoiGUI):
    async with app.run_test(headless=False, notifications=True) as pilot:
        await pilot.pause(PMTimeOut.start_stop.value)
        tabbed_content = pilot.app.screen.query_exactly_one(TabbedContent)
        for label in TabLabel.main_tabs():
            await click_tab(pilot, label, tabbed_content)
            await test_binding(pilot, "M")
        for label in TabLabel.operate_tabs():
            await click_tab(pilot, label, tabbed_content)
            await test_binding(pilot, "D")
            await test_binding(pilot, "F")
        await click_tab(pilot, TabLabel.apply, tabbed_content)
        await pilot.pause(PMTimeOut.start_stop.value)
        await pilot.exit(None)
