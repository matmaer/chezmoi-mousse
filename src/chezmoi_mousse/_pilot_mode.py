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
    final = 6.0
    initial = 5.0


async def test_binding(pilot: Pilot[None], key: str):
    await pilot.pause(PMTimeOut.min_pause.value)
    await pilot.press(key)
    await pilot.wait_for_animation()
    await pilot.pause(PMTimeOut.min_pause.value)
    await pilot.press(key)
    await pilot.wait_for_animation()
    await pilot.pause(PMTimeOut.min_pause.value)


async def click_tab(
    pilot: Pilot[None], label: TabLabel, tabbed_content: TabbedContent
) -> None:
    tab = tabbed_content.get_tab(label)
    await pilot.pause(PMTimeOut.min_pause.value)
    await pilot.click(tab)
    await pilot.wait_for_animation()
    await pilot.pause(PMTimeOut.min_pause.value)


async def test_app_with_pilot(app: ChezmoiGUI):
    async with app.run_test(headless=False, notifications=True) as pilot:
        await pilot.pause(PMTimeOut.initial.value)
        tabbed_content = pilot.app.screen.query_exactly_one(TabbedContent)
        for label in TabLabel.main_tab_labels():
            await click_tab(pilot, label, tabbed_content)
            await test_binding(pilot, "M")
        for label in TabLabel.operate_tabs():
            await click_tab(pilot, label, tabbed_content)
            await test_binding(pilot, "D")
            await test_binding(pilot, "F")
        await click_tab(pilot, TabLabel.apply, tabbed_content)
        await pilot.pause(PMTimeOut.final.value)
        await pilot.exit(None)
