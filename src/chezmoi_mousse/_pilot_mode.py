"""Module for testing the application by interfacing programmatically.

This is work in progress and only contains very basic tests for now.
"""

from __future__ import annotations

import asyncio
import random
from itertools import product
from typing import TYPE_CHECKING

from textual.pilot import Pilot
from textual.widget import Widget
from textual.widgets import Switch, TabbedContent, TabPane

from ._cmd_results import DirContentBtn
from ._str_enums import TabLabel
from .gui.common.actionables import FlatButton, OpButton, SwitchSlider, TabButton
from .gui.common.diffs import DiffView
from .gui.common.loading_modal import LoadingModal

if TYPE_CHECKING:
    from textual.message import Message

    from .gui.textual_app import ChezmoiGUI

from .gui.common.messages import ReadyToUseMsg


async def pilot_chill(pilot: Pilot[None]):
    await pilot.wait_for_scheduled_animations()
    while isinstance(pilot.app.screen, LoadingModal):
        await pilot.pause(0.2)
    await pilot.pause(0.2)


async def click_and_wait(pilot: Pilot[None], widget: Widget) -> None:
    await pilot.click(widget)
    await pilot_chill(pilot)


async def press_and_wait(pilot: Pilot[None], key: str) -> None:
    await pilot.press(key)
    await pilot_chill(pilot)


async def toggle_binding(pilot: Pilot[None], key: str):
    await press_and_wait(pilot, key)
    await press_and_wait(pilot, key)


async def refresh_trees(pilot: Pilot[None], active_pane: TabPane) -> None:
    if active_pane.id not in (TabLabel.apply, TabLabel.re_add, TabLabel.add):
        return
    op_buttons = active_pane.query(OpButton).results()
    refresh_tree_btn = next((b for b in op_buttons if "Refresh" in str(b.label)), None)
    reload_button = next((b for b in op_buttons if "Reload" in str(b.label)), None)
    if refresh_tree_btn is None or reload_button is None:
        raise ValueError("Operate buttons not found")
    await click_and_wait(pilot, refresh_tree_btn)
    await click_and_wait(pilot, reload_button)


async def toggle_switches(pilot: Pilot[None], active_pane: TabPane) -> None:
    if active_pane.id not in (TabLabel.apply, TabLabel.re_add, TabLabel.add):
        return
    switch_slider = active_pane.query_exactly_one(SwitchSlider)
    switches: tuple[Switch, ...] = tuple(switch_slider.query(Switch))

    states = list(product((False, True), repeat=len(switches)))[1:]
    rev_states = list(reversed(states))

    for state in states + rev_states:
        for switch, target in zip(switches, state, strict=True):
            if switch.value != target:
                await click_and_wait(pilot, switch)


async def click_content_switcher_buttons(pilot: Pilot[None], tab_pane: TabPane) -> None:
    tab_buttons = tuple(tab_pane.query(TabButton).results())
    for tab_button in tab_buttons[1:]:
        await click_and_wait(pilot, tab_button)
    flat_buttons = tuple(tab_pane.query(FlatButton).results())
    for flat_button in flat_buttons[1:]:
        await click_and_wait(pilot, flat_button)


async def click_random_path_in_diff_view(pilot: Pilot[None], tab_pane: TabPane) -> None:
    if tab_pane.id not in (TabLabel.apply, TabLabel.re_add):
        return
    diff_view = tab_pane.query_exactly_one(DiffView)
    diff_view_clickable_paths = tuple(diff_view.query(DirContentBtn).results())
    # choose a random path to click on
    if not diff_view_clickable_paths:
        await pilot_chill(pilot)
        return
    to_click = random.choice(diff_view_clickable_paths)
    await click_and_wait(pilot, to_click)


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
            tab = tabbed_content.get_tab(label)
            await click_and_wait(pilot, tab)
            await toggle_binding(pilot, "M")
            await toggle_binding(pilot, "D")
            await toggle_binding(pilot, "F")
            tab_pane = tabbed_content.active_pane
            if tab_pane is None:
                raise ValueError("No active pane")
            await click_random_path_in_diff_view(pilot, tab_pane)
            await click_content_switcher_buttons(pilot, tab_pane)
            await toggle_switches(pilot, tab_pane)
            await refresh_trees(pilot, tab_pane)
        tab = tabbed_content.get_tab(TabLabel.apply)
        await click_and_wait(pilot, tab)
        await pilot.exit(None)
