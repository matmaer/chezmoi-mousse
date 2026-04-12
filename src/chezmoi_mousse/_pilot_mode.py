"""Module for testing the application by interfacing programmatically.

This is work in progress.
Source for the Pilot class is here: textual/pilot.py
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from textual.pilot import Pilot
from textual.widgets import TabbedContent

from ._str_enums import TabLabel

if TYPE_CHECKING:
    from textual.message import Message

    from .gui.textual_app import ChezmoiGUI

from .gui.common.messages import ReadyToUseMsg


async def pilot_chill(pilot: Pilot[None]):
    await pilot.pause(0.05)
    await pilot.wait_for_scheduled_animations()
    await pilot.pause(0.05)


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
    ready_event = asyncio.Event()

    def message_hook(message: Message) -> None:
        # Called for every message delivered while running under run_test
        if isinstance(message, ReadyToUseMsg):
            ready_event.set()

    async with app.run_test(
        headless=False, notifications=True, message_hook=message_hook
    ) as pilot:
        # wait until ReadyToUseMsg is observed
        await ready_event.wait()
        tabbed_content = pilot.app.screen.query_exactly_one(TabbedContent)
        for label in TabLabel.main_tabs():
            await click_tab(pilot, label, tabbed_content)
            await test_binding(pilot, "M")
        for label in TabLabel.operate_tabs():
            await click_tab(pilot, label, tabbed_content)
            await test_binding(pilot, "D")
            await test_binding(pilot, "F")
        await click_tab(pilot, TabLabel.apply, tabbed_content)
        await pilot_chill(pilot)
        await pilot.exit(None)
