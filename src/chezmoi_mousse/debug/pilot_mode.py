"""Module for testing the application by interfacing programmatically."""

from __future__ import annotations

import asyncio
import random
from typing import TYPE_CHECKING

from textual.widgets import (
    Button,
    Collapsible,
    RadioButton,
    RadioSet,
    Switch,
    Tab,
    TabbedContent,
    TabPane,
)
from textual.widgets.collapsible import CollapsibleTitle

from chezmoi_mousse.debug.debug_tab import DebugTab
from chezmoi_mousse.gui.common.actionables import FlatButtonsVertical, TabButtons
from chezmoi_mousse.gui.common.operate_modal import OperateModal
from chezmoi_mousse.gui.common.operate_tree import OperateTree
from chezmoi_mousse.gui.config_tab import ConfigTab
from chezmoi_mousse.gui.logs_tab import LogsTab
from chezmoi_mousse.gui.operate_tab import OperateTab
from chezmoi_mousse.gui.splash_screen import SplashScreen
from chezmoi_mousse.str_enums import BtnLabel, ChezmoiPrompts, Tcss

__all__ = ["run_with_pilot"]

type HoverClickTypes = Button | RadioButton | Switch | CollapsibleTitle | Tab
CHILL_TIME = 0.1

if TYPE_CHECKING:
    from textual.pilot import Pilot
    from textual.widget import Widget

    from chezmoi_mousse.gui.textual_app import ChezmoiGui


async def _hover_and_click(pilot: Pilot[object], widget: HoverClickTypes) -> None:
    if widget.is_on_screen and widget.display and widget.is_parent_active:
        await pilot.pause(CHILL_TIME)
        if widget.screen.scroll_to_widget(widget):
            await pilot.wait_for_scheduled_animations()
        await pilot.hover(widget)
        await pilot.pause(CHILL_TIME)
        await pilot.click(widget)
        await pilot.wait_for_animation()


async def _press_key(pilot: Pilot[object], key: str) -> None:
    await pilot.pause(CHILL_TIME)
    await pilot.press(key)
    await pilot.wait_for_animation()


async def _toggle_bindings(pilot: Pilot[object], tab_pane: TabPane) -> None:
    for key in "CTM":
        if not isinstance(tab_pane, OperateTab) and key in "CT":
            continue
        await _press_key(pilot, key)
        await _press_key(pilot, key)


async def _scroll_widget(pilot: Pilot[object], widget: Widget) -> None:
    await pilot.pause(CHILL_TIME)
    if widget.is_scrollable and widget.scrollbars_enabled and widget.display:
        if widget.show_horizontal_scrollbar:
            if widget.is_horizontal_scroll_end:
                widget.scroll_left()
            else:
                widget.scroll_right()
        if widget.show_vertical_scrollbar:
            if widget.is_vertical_scroll_end:
                widget.scroll_up()
            else:
                widget.scroll_down()
        await pilot.wait_for_animation()


async def _toggle_random_collapsible(pilot: Pilot[object], root: Widget) -> None:
    collapsibles = [c for c in root.query(Collapsible) if c.collapsed]
    if collapsibles:
        to_toggle = random.choice(collapsibles)
        c_title = to_toggle.query_exactly_one(CollapsibleTitle)
        await _hover_and_click(pilot, c_title)
        await _scroll_widget(pilot, to_toggle)
        await _hover_and_click(pilot, c_title)


async def _scroll_random_widget(pilot: Pilot[object], root: Widget) -> None:
    scrollables = [
        w
        for w in root.query()
        if w.is_scrollable and w.scrollbars_enabled and w.display
    ]
    if scrollables:
        await _scroll_widget(pilot, random.choice(scrollables))


async def _click_content_switchers(pilot: Pilot[object], tab_pane: TabPane) -> None:
    content_switchers = [
        w
        for w in tab_pane.query()
        if isinstance(w, (FlatButtonsVertical, TabButtons, RadioSet))
    ]
    for cs in content_switchers:
        for button in cs.query_children(Button):
            await _hover_and_click(pilot, button)
            await _toggle_random_collapsible(pilot, tab_pane)
            await _scroll_random_widget(pilot, tab_pane)


async def _explore_operate_tab(pilot: Pilot[object], op_tab: OperateTab) -> None:
    cm_theme = pilot.app.theme
    textual_dark = "textual-dark"
    themes = pilot.app.available_themes.items()
    dark_themes = {name for name, theme in themes if theme.dark}
    random_dark = random.choice(list(dark_themes - {cm_theme, textual_dark}))

    for theme_name in [cm_theme, textual_dark, random_dark, cm_theme]:
        pilot.app.theme = theme_name
        await pilot.wait_for_scheduled_animations()
        await _run_operate_round(pilot, op_tab)


async def _run_operate_round(pilot: Pilot[object], tab_pane: OperateTab) -> None:
    switches = [
        switch
        for switch in tab_pane.query(Switch)
        if switch.is_on_screen and not switch.disabled
    ]
    if switches:
        await _hover_and_click(pilot, random.choice(switches))

    for tree in tab_pane.query(OperateTree):
        if not tree.is_on_screen:
            continue
        tree.focus()
        for _ in range(random.randint(1, 4)):
            await _press_key(pilot, random.choice(("up", "down", "right", "left")))
        node = tree.cursor_node
        if (
            node is not None
            and node.data is not None
            and (node.data.managed or node.data.wanted is not False)
        ):
            await _press_key(pilot, "enter")
        break

    radio_buttons = list(tab_pane.query(RadioButton).results())
    if radio_buttons:
        await _hover_and_click(pilot, random.choice(radio_buttons))
    if random.random() < 0.3:
        header_buttons = [
            button
            for button in tab_pane.query(f".{Tcss.tree_header} Button").results(Button)
            if button.is_on_screen and not button.disabled
        ]
        if header_buttons:
            await _hover_and_click(pilot, random.choice(header_buttons))
    await _scroll_random_widget(pilot, tab_pane)
    if random.random() < 0.3:
        await _explore_operate_modal(pilot, tab_pane)


async def _explore_operate_modal(pilot: Pilot[object], tab_pane: OperateTab) -> None:
    buttons = [
        button
        for button in tab_pane.query(Button)
        if button.label in BtnLabel.op_btn_labels()
        and button.is_on_screen
        and not button.disabled
    ]
    if not buttons:
        return
    await _hover_and_click(pilot, random.choice(buttons))
    modal = pilot.app.screen
    if not isinstance(modal, OperateModal):
        raise RuntimeError("Operation button did not open the operate modal")

    run_command = random.choice((True, False))
    safe_labels = {
        prompt.prompt_item
        for prompt in ChezmoiPrompts
        if prompt.reply in ChezmoiPrompts.non_operation_replies()
    }
    async with asyncio.timeout(20):
        while pilot.app.screen is modal:
            await _toggle_random_collapsible(pilot, modal)
            await _scroll_random_widget(pilot, modal)
            available = {
                str(button.label): button
                for button in modal.query(Button)
                if button.is_on_screen and not button.disabled
            }
            safe_buttons = [
                button for label, button in available.items() if label in safe_labels
            ]
            if BtnLabel.close in available:
                await _hover_and_click(pilot, available[BtnLabel.close])
            elif safe_buttons:
                await _hover_and_click(pilot, random.choice(safe_buttons))
            elif run_command and modal.op_btn.run_label in available:
                await _hover_and_click(pilot, available[modal.op_btn.run_label])
            elif BtnLabel.cancel in available:
                await _hover_and_click(pilot, available[BtnLabel.cancel])
            else:
                await asyncio.sleep(CHILL_TIME)


async def _test_path_operations(pilot: Pilot[object], tab_pane: DebugTab) -> None:
    buttons = {button.label: button for button in tab_pane.query(Button)}
    await _hover_and_click(pilot, buttons[BtnLabel.test_paths])
    action = random.choice(
        (BtnLabel.create_diffs, BtnLabel.remove_paths, BtnLabel.reset_paths)
    )
    await _hover_and_click(pilot, buttons[action])
    await _hover_and_click(pilot, buttons[BtnLabel.list_paths])
    if action == BtnLabel.remove_paths:
        await _hover_and_click(pilot, buttons[BtnLabel.reset_paths])
    await _hover_and_click(pilot, buttons[BtnLabel.create_diffs])
    await _hover_and_click(pilot, buttons[BtnLabel.list_paths])


def run_with_pilot(app: ChezmoiGui) -> None:
    app.run(auto_pilot=_start_pilot_mode)


async def _start_pilot_mode(pilot: Pilot[object]) -> None:
    await asyncio.sleep(0.5)
    while isinstance(pilot.app.screen, SplashScreen):
        await asyncio.sleep(CHILL_TIME)

    await pilot.wait_for_scheduled_animations()
    tabbed_content = pilot.app.screen.query_exactly_one(TabbedContent)

    for tab_pane in tabbed_content.query(TabPane):
        tab = tabbed_content.get_tab(tab_pane)
        await _hover_and_click(pilot, tab)
        if isinstance(tab_pane, OperateTab):
            await _explore_operate_tab(pilot, tab_pane)
        elif isinstance(tab_pane, (LogsTab, ConfigTab)):
            await _click_content_switchers(pilot, tab_pane)
        elif isinstance(tab_pane, DebugTab):
            await _click_content_switchers(pilot, tab_pane)
            await _test_path_operations(pilot, tab_pane)
        await _toggle_bindings(pilot, tab_pane)
        await _toggle_random_collapsible(pilot, tab_pane)
        await _scroll_random_widget(pilot, tab_pane)

    operate_tab = tabbed_content.query_exactly_one(OperateTab)
    await _hover_and_click(pilot, tabbed_content.get_tab(operate_tab))
    refresh_button = operate_tab.query_exactly_one(f".{Tcss.refresh_button}", Button)
    await _hover_and_click(pilot, refresh_button)
    pilot.app.notify("Pilot mode completed.")
