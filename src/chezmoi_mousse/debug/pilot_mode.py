"""Module for testing the application by interfacing programmatically."""

from __future__ import annotations

import asyncio
import random
from itertools import product
from typing import TYPE_CHECKING

from textual.pilot import OutOfBounds, Pilot
from textual.widget import Widget
from textual.widgets import Switch, TabbedContent, TabPane

from chezmoi_mousse.gui.common.actionables import (
    DirContentBtn,
    FlatButton,
    OpButton,
    SwitchSlider,
    TabButton,
)
from chezmoi_mousse.gui.common.diffs import DiffView
from chezmoi_mousse.gui.common.loading_modal import LoadingModal
from chezmoi_mousse.gui.tab_panes import AddTab, ApplyTab, ReAddTab
from chezmoi_mousse.str_enums import TabLabel

if TYPE_CHECKING:

    from chezmoi_mousse.textual_app import ChezmoiGui


async def pilot_chill(pilot: Pilot[str]):
    await pilot.wait_for_scheduled_animations()
    while isinstance(pilot.app.screen, LoadingModal):
        await pilot.pause(0.2)
    await pilot.pause(0.2)


async def click_and_wait(pilot: Pilot[str], widget: Widget) -> None:
    try:
        await pilot.click(widget)
        await pilot_chill(pilot)
    except OutOfBounds:
        pilot.app.notify(f"widget {widget} not in view", severity="error")
        await pilot_chill(pilot)
        return


async def press_and_wait(pilot: Pilot[str], key: str) -> None:
    await pilot.press(key)
    await pilot_chill(pilot)


async def toggle_binding(pilot: Pilot[str], key: str):
    await press_and_wait(pilot, key)
    await press_and_wait(pilot, key)


async def refresh_trees(pilot: Pilot[str], active_pane: TabPane) -> None:
    if not isinstance(active_pane, (ApplyTab, ReAddTab, AddTab)):
        return
    refresh_tree_btn = active_pane.query_one(
        active_pane.ids.op_btn.refresh_tree_q, OpButton
    )
    reload_button = active_pane.query_one(active_pane.ids.op_btn.reload_q, OpButton)
    await click_and_wait(pilot, refresh_tree_btn)
    await click_and_wait(pilot, reload_button)


async def toggle_switches(pilot: Pilot[str], active_pane: TabPane) -> None:
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


async def click_content_switcher_buttons(pilot: Pilot[str], tab_pane: TabPane) -> None:
    tab_buttons = tuple(tab_pane.query(TabButton).results())
    for tab_button in tab_buttons[1:]:
        await click_and_wait(pilot, tab_button)
    flat_buttons = tuple(tab_pane.query(FlatButton).results())
    for flat_button in flat_buttons[1:]:
        await click_and_wait(pilot, flat_button)


async def click_random_path_in_diff_view(pilot: Pilot[str], tab_pane: TabPane) -> None:
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


def run_with_pilot(app: ChezmoiGui):
    asyncio.run(start_pilot_mode(app))


async def start_pilot_mode(app: ChezmoiGui):
    async with app.run_test(headless=False, notifications=True) as pilot:
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
        await pilot.exit("Pilot mode completed\n")
