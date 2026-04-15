"""Module for testing the application by interfacing programmatically.

This is work in progress and only contains very basic tests for now.
"""

from __future__ import annotations

import asyncio
from itertools import product
from typing import TYPE_CHECKING

from textual.pilot import Pilot
from textual.widget import Widget
from textual.widgets import Button, Switch, TabbedContent, TabPane

from ._str_enums import TabLabel
from .gui.common.actionables import SwitchSlider

if TYPE_CHECKING:
    from textual.message import Message

    from .gui.textual_app import ChezmoiGUI

from .gui.common.messages import ReadyToUseMsg


async def pilot_chill(pilot: Pilot[None]):
    await pilot.wait_for_scheduled_animations()
    await pilot.pause(0.05)


async def click_and_wait(pilot: Pilot[None], widget: Widget) -> None:
    await pilot.click(widget)
    await pilot_chill(pilot)


async def press_and_wait(pilot: Pilot[None], key: str) -> None:
    await pilot.press(key)
    await pilot_chill(pilot)


async def refresh_trees(pilot: Pilot[None], active_pane: TabPane | None) -> None:
    if active_pane is None:
        raise ValueError("No active pane")
    buttons = active_pane.query(Button).results()
    refresh_tree_btn = next(
        (btn for btn in buttons if "Refresh" in str(btn.label)), None
    )
    if refresh_tree_btn is None:
        raise ValueError("No refresh tree button found")
    else:
        pilot.app.notify(f"Found refresh tree button: {refresh_tree_btn}")


async def toggle_binding(pilot: Pilot[None], key: str):
    await press_and_wait(pilot, key)
    await press_and_wait(pilot, key)


async def toggle_switches(pilot: Pilot[None], active_pane: TabPane | None) -> None:
    if active_pane is None:
        raise ValueError("No active pane")
    switch_slider = active_pane.query_exactly_one(SwitchSlider)
    switches: tuple[Switch, ...] = tuple(switch_slider.query(Switch))

    async def set_state(state: tuple[bool, ...]) -> None:
        for switch, target in zip(switches, state, strict=True):
            if switch.value != target:
                await click_and_wait(pilot, switch)

    states = list(product((False, True), repeat=len(switches)))

    # We have to cover all transitions as we add and remove nodes in the Tree widgets,
    # so we build the complete directed graph excluding self-loops (A → A) when nothing
    # changes. Every other (prev → next) edge exists once.
    # Hierholzer's algorithm finds an Eulerian circuit covering all edges
    # exactly once, so every meaningful ordered transition should be covered.
    graph = {state: [s for s in states if s != state] for state in states}
    stack = [states[0]]
    circuit: list[tuple[bool, ...]] = []
    while stack:
        v = stack[-1]
        if graph[v]:
            stack.append(graph[v].pop())
        else:
            circuit.append(stack.pop())
    circuit.reverse()

    for state in circuit[1:-1]:
        await set_state(state)


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
            if label in TabLabel.operate_tabs():
                await toggle_binding(pilot, "D")
                await toggle_binding(pilot, "F")
                await toggle_switches(pilot, tabbed_content.active_pane)
                await refresh_trees(pilot, tabbed_content.active_pane)
        tab = tabbed_content.get_tab(TabLabel.apply)
        await click_and_wait(pilot, tab)
        await pilot.exit(None)
