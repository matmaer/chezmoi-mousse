"""Module for testing the application by interfacing programmatically."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from textual.pilot import OutOfBounds
from textual.widgets import TabbedContent

from chezmoi_mousse.gui.common.actionables import (
    FlatBtn,
    TabBtn,
)
from chezmoi_mousse.gui.splash_screen import SplashScreen
from chezmoi_mousse.str_enums import BtnLabel

__all__ = ["run_with_pilot"]

if TYPE_CHECKING:
    from textual.pilot import Pilot
    from textual.widget import Widget
    from textual.widgets import TabPane

    from chezmoi_mousse.gui.textual_app import ChezmoiGui


async def _pilot_chill(pilot: Pilot[str]) -> None:

    await pilot.wait_for_scheduled_animations()
    while isinstance(pilot.app.screen, SplashScreen):
        await pilot.pause(0.1)
    await pilot.pause(0.1)


async def _click_and_wait(pilot: Pilot[str], widget: Widget) -> None:
    try:
        await pilot.click(widget)
        await _pilot_chill(pilot)
    except OutOfBounds:
        pilot.app.notify(f"widget {widget} not in view", severity="error")
        await _pilot_chill(pilot)
        return


async def _press_and_wait(pilot: Pilot[str], key: str) -> None:
    await pilot.press(key)
    await _pilot_chill(pilot)


async def _toggle_binding(pilot: Pilot[str], key: str) -> None:
    await _press_and_wait(pilot, key)
    await _press_and_wait(pilot, key)


async def _click_content_switcher_buttons(pilot: Pilot[str], tab_pane: TabPane) -> None:
    tab_buttons = tuple(tab_pane.query(TabBtn).results())
    for tab_button in tab_buttons[1:]:
        await _click_and_wait(pilot, tab_button)
    flat_buttons = tuple(tab_pane.query(FlatBtn).results())
    for flat_button in flat_buttons[1:]:
        await _click_and_wait(pilot, flat_button)


def run_with_pilot(app: ChezmoiGui) -> None:
    asyncio.run(_start_pilot_mode(app))


async def _start_pilot_mode(app: ChezmoiGui) -> None:

    async with app.run_test(headless=False, notifications=True) as pilot:
        await asyncio.sleep(0.5)
        while isinstance(pilot.app.screen, SplashScreen):
            await asyncio.sleep(0.2)
            await _pilot_chill(pilot)

        await _pilot_chill(pilot)
        tabbed_content = pilot.app.screen.query_exactly_one(TabbedContent)

        tabs_to_check = [
            BtnLabel.operate,
            BtnLabel.add,
            BtnLabel.logs,
            BtnLabel.config,
        ]

        if "debug" in app.features:
            tabs_to_check.append(BtnLabel.debug)

        for label in tabs_to_check:
            await _pilot_chill(pilot)
            tab = tabbed_content.get_tab(label)
            await _click_and_wait(pilot, tab)
            await _toggle_binding(pilot, "M")
            await _toggle_binding(pilot, "D")
            await _toggle_binding(pilot, "F")
            tab_pane = tabbed_content.active_pane
            if tab_pane is None:
                raise ValueError("No active pane")
            await _click_content_switcher_buttons(pilot, tab_pane)

        await pilot.exit("Pilot mode completed\n")
