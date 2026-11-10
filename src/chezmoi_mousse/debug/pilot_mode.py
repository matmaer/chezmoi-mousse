"""Module for testing the application by interfacing programmatically."""

from __future__ import annotations

import asyncio
import random
from collections import deque
from typing import TYPE_CHECKING

from textual.widgets import Button, RadioButton, RadioSet, Switch, Tab, TabbedContent
from textual.widgets.collapsible import CollapsibleTitle

from chezmoi_mousse.debug.debug_tab import DebugTab
from chezmoi_mousse.debug.pilot_funcs import NoChill, WithChill
from chezmoi_mousse.gui.common.actionables import (
    FlatBtnGroup,
    SwitchGroup,
    TreeBtnGroup,
)
from chezmoi_mousse.gui.common.operate_modal import OperateModal
from chezmoi_mousse.gui.common.operate_tree import OperateTree
from chezmoi_mousse.gui.config_tab import ConfigTab
from chezmoi_mousse.gui.logs_tab import LogsTab
from chezmoi_mousse.gui.operate_tab import OperateTab
from chezmoi_mousse.gui.splash_screen import SplashScreen
from chezmoi_mousse.str_enums import BtnLabel, ChezmoiPrompts

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from textual.pilot import Pilot
    from textual.widgets import TabPane
    from textual.widgets.tree import TreeNode

    from chezmoi_mousse.data_types import NodeData
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

type HoverClickTypes = Button | RadioButton | Switch | CollapsibleTitle | Tab

__all__ = ["run_with_pilot"]


async def _explore_tabs(pilot: Pilot[object], tab_pane: TabPane) -> None:
    await NoChill.toggle_bindings(pilot, tab_pane)
    if isinstance(tab_pane, OperateTab):
        await _explore_operate_tab(pilot, tab_pane)
    elif isinstance(tab_pane, LogsTab):
        for _ in range(3):
            await WithChill.toggle_random_collapsible_and_scroll(pilot, tab_pane)

    elif isinstance(tab_pane, (ConfigTab, DebugTab)):
        flat_btn_group = tab_pane.query_exactly_one(FlatBtnGroup)
        buttons = deque(flat_btn_group.query_children(Button).results())
        buttons.rotate(-1)
        for button in buttons:
            await WithChill.hover_and_click(pilot, button)
            await NoChill.scroll_relevant_widget(pilot, tab_pane)


async def _explore_operate_tab(pilot: Pilot[object], op_tab: OperateTab) -> None:
    radio_set = op_tab.query_exactly_one(RadioSet)
    buttons: Iterator[RadioButton] = radio_set.query_children(RadioButton).results()
    items = deque(buttons)
    items.rotate(-1)
    for button in items:
        op_tab.current_displayed_tree.focus()
        await WithChill.select_random_tree_node(pilot, op_tab.current_displayed_tree)
        radio_set.focus()
        await WithChill.hover_and_click(pilot, button)
    switch_group = pilot.app.query_exactly_one(SwitchGroup)
    switch_buttons = list(switch_group.query_children(Switch).results())
    for btn in switch_buttons:
        await WithChill.hover_and_click(pilot, btn)
    for btn in reversed(switch_buttons):
        await WithChill.hover_and_click(pilot, btn)

    tree_btn_group = op_tab.query_exactly_one(TreeBtnGroup)

    def any_expanded(node_map: dict[Path, TreeNode[NodeData]]) -> bool:
        return any(
            n
            for n in node_map.values()
            if not n.is_root and n.allow_expand and n.is_expanded
        )

    def any_collapsed(node_map: dict[Path, TreeNode[NodeData]]) -> bool:
        return any(
            n
            for n in node_map.values()
            if not n.is_root and n.allow_expand and n.is_collapsed
        )

    while any_collapsed(op_tab.current_displayed_tree.node_map):
        await WithChill.click_tree_btn(pilot, tree_btn_group.expand_btn)

    while any_expanded(op_tab.current_displayed_tree.node_map):
        await WithChill.click_tree_btn(pilot, tree_btn_group.collapse_btn)


async def _test_path_operations(pilot: Pilot[object], debug_tab: DebugTab) -> None:
    buttons = {button.label: button for button in debug_tab.query(Button)}
    await WithChill.hover_and_click(pilot, buttons[BtnLabel.list_paths])
    await WithChill.hover_and_click(pilot, buttons[BtnLabel.create_diffs])
    await WithChill.hover_and_click(pilot, buttons[BtnLabel.list_paths])


async def _set_random_operate_tab_state(
    pilot: Pilot[object], op_tab: OperateTab
) -> None:
    switches = [
        switch
        for switch in op_tab.query(Switch)
        if switch.is_on_screen and not switch.disabled
    ]
    if switches:
        await WithChill.hover_and_click(pilot, random.choice(switches))

    for tree in op_tab.query(OperateTree):
        if not tree.is_on_screen:
            continue
        tree.focus()
        for _ in range(random.randint(1, 8)):
            await NoChill.press_key(
                pilot, random.choice(("up", "down", "right", "left"))
            )
        node = tree.cursor_node
        if (
            node is not None
            and node.data is not None
            and (node.data.managed or node.data.wanted is not False)
        ):
            await NoChill.press_key(pilot, "enter")
        break

    radio_buttons = list(op_tab.query(RadioButton).results())
    if radio_buttons:
        await WithChill.hover_and_click(pilot, random.choice(radio_buttons))


async def _run_op_round(pilot: Pilot[object], tabbed_content: TabbedContent) -> None:
    operate_tab = tabbed_content.query_exactly_one(OperateTab)
    op_tab_btn = tabbed_content.get_tab(operate_tab)

    debug_tab = tabbed_content.query_exactly_one(DebugTab)
    debug_tab_btn = tabbed_content.get_tab(debug_tab)

    await WithChill.hover_and_click(pilot, op_tab_btn)
    await _set_random_operate_tab_state(pilot, operate_tab)

    await WithChill.hover_and_click(pilot, debug_tab_btn)
    await _test_path_operations(pilot, debug_tab)

    await WithChill.hover_and_click(pilot, op_tab_btn)
    await _run_operation(pilot, operate_tab)


async def _run_operation(pilot: Pilot[object], op_tab: OperateTab) -> None:
    op_buttons = [
        button for button in op_tab.op_btn_group.query(Button) if not button.disabled
    ]
    if not op_buttons:
        return
    await WithChill.hover_and_click(pilot, random.choice(op_buttons))
    modal = pilot.app.screen
    if not isinstance(modal, OperateModal):
        raise RuntimeError("Operation button did not open the operate modal")

    run_command = random.choice((True, False))
    safe_labels = {
        prompt.prompt_item
        for prompt in ChezmoiPrompts
        if prompt.reply in ChezmoiPrompts.non_operation_replies()
    }
    while pilot.app.screen is modal:
        await WithChill.toggle_random_collapsible_and_scroll(pilot, modal)
        available = {
            str(button.label): button
            for button in modal.query(Button)
            if button.is_on_screen and not button.disabled
        }
        safe_buttons = [
            button for label, button in available.items() if label in safe_labels
        ]
        if BtnLabel.close in available:
            await WithChill.hover_and_click(pilot, available[BtnLabel.close])
        elif safe_buttons:
            await WithChill.hover_and_click(pilot, random.choice(safe_buttons))
        elif run_command and modal.op_btn.run_label in available:
            await WithChill.hover_and_click(pilot, available[modal.op_btn.run_label])
        elif BtnLabel.cancel in available:
            await WithChill.hover_and_click(pilot, available[BtnLabel.cancel])


def run_with_pilot(app: ChezmoiGui) -> None:
    app.run(auto_pilot=_run_pilot_mode)


async def _run_pilot_mode(pilot: Pilot[object]) -> None:
    while isinstance(pilot.app.screen, SplashScreen):
        await asyncio.sleep(0.1)
    await pilot.wait_for_scheduled_animations()

    tabbed_content = pilot.app.screen.query_exactly_one(TabbedContent)
    await tabbed_content.wait_for_refresh()

    operate_tab = tabbed_content.query_exactly_one(OperateTab)
    logs_tab = tabbed_content.query_exactly_one(LogsTab)
    config_tab = tabbed_content.query_exactly_one(ConfigTab)
    debug_tab = tabbed_content.query_exactly_one(DebugTab)

    for tab_pane in (operate_tab, logs_tab, config_tab, debug_tab):
        tab = tabbed_content.get_tab(tab_pane)
        await WithChill.hover_and_click(pilot, tab)
        await _explore_tabs(pilot, tab_pane)

    cm_theme = pilot.app.theme
    themes = pilot.app.available_themes.items()
    dark_themes = {name for name, theme in themes if theme.dark}
    random_dark = random.choice(list(dark_themes - {cm_theme}))

    for theme_name in [cm_theme, random_dark, cm_theme]:
        pilot.app.theme = theme_name
        await pilot.wait_for_scheduled_animations()
        await _run_op_round(pilot, tabbed_content)

    pilot.app.notify("Pilot mode completed.")
