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
)
from textual.widgets.collapsible import CollapsibleTitle

from chezmoi_mousse.debug.debug_tab import DebugTab
from chezmoi_mousse.gui.common.actionables import (
    FlatButtonsVertical,
    TabButtons,
    TreeButtons,
)
from chezmoi_mousse.gui.common.operate_modal import OperateModal
from chezmoi_mousse.gui.common.operate_tree import OperateTree
from chezmoi_mousse.gui.config_tab import ConfigTab
from chezmoi_mousse.gui.logs_tab import LogsTab
from chezmoi_mousse.gui.operate_tab import OperateTab
from chezmoi_mousse.gui.splash_screen import SplashScreen
from chezmoi_mousse.str_enums import BtnLabel, ChezmoiPrompts

__all__ = ["run_with_pilot"]

type HoverClickTypes = Button | RadioButton | Switch | CollapsibleTitle | Tab

CHILL_TIME = 0.1

if TYPE_CHECKING:
    from textual.pilot import Pilot
    from textual.widget import Widget
    from textual.widgets import TabPane

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
    while not widget.is_horizontal_scroll_end:
        widget.scroll_right()
        await asyncio.sleep(CHILL_TIME / 100)
    await pilot.wait_for_scheduled_animations()
    if not widget.is_vertical_scroll_end:
        widget.scroll_end()
        await pilot.wait_for_scheduled_animations()
    widget.scroll_home()
    await pilot.wait_for_scheduled_animations()


async def _toggle_random_collapsible(pilot: Pilot[object], root: Widget) -> None:
    collapsibles = [c for c in root.query(Collapsible) if c.collapsed]
    if collapsibles:
        await pilot.pause(CHILL_TIME)
        to_toggle = random.choice(collapsibles)
        c_title = to_toggle.query_exactly_one(CollapsibleTitle)
        await _hover_and_click(pilot, c_title)
        await _scroll_widget(pilot, to_toggle)
        await _hover_and_click(pilot, c_title)


async def _scroll_random_widget(pilot: Pilot[object], root: Widget) -> None:
    scrollables = [
        w
        for w in root.query()
        if w.is_scrollable
        and w.display
        and w.is_on_screen
        and (w.show_vertical_scrollbar or w.show_horizontal_scrollbar)
    ]
    if scrollables:
        await _scroll_widget(pilot, random.choice(scrollables))


async def _explore_all_tabs_basic(pilot: Pilot[object], tab_pane: TabPane) -> None:
    await _toggle_bindings(pilot, tab_pane)
    button_groups = [
        w
        for w in tab_pane.query()
        if isinstance(w, (FlatButtonsVertical, TabButtons, RadioSet))
    ]
    for btn_group in button_groups:
        if isinstance(btn_group, RadioSet):
            buttons = btn_group.query_children(RadioButton)
        else:
            buttons = btn_group.query(Button)
        for index, button in enumerate(buttons):
            if index != 0:
                await _hover_and_click(pilot, button)
            await _toggle_random_collapsible(pilot, tab_pane)
            if random.random() < 0.33:
                await _scroll_random_widget(pilot, tab_pane)
        await _hover_and_click(pilot, buttons[0])


async def _test_path_operations(pilot: Pilot[object], debug_tab: DebugTab) -> None:
    buttons = {button.label: button for button in debug_tab.query(Button)}
    await _hover_and_click(pilot, buttons[BtnLabel.list_paths])
    await _hover_and_click(pilot, buttons[BtnLabel.create_diffs])
    await _hover_and_click(pilot, buttons[BtnLabel.list_paths])


async def _set_random_operate_tab_state(
    pilot: Pilot[object], op_tab: OperateTab
) -> None:
    switches = [
        switch
        for switch in op_tab.query(Switch)
        if switch.is_on_screen and not switch.disabled
    ]
    if switches:
        await _hover_and_click(pilot, random.choice(switches))

    for tree in op_tab.query(OperateTree):
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

    radio_buttons = list(op_tab.query(RadioButton).results())
    if radio_buttons:
        await _hover_and_click(pilot, random.choice(radio_buttons))


async def _run_op_round(pilot: Pilot[object], tabbed_content: TabbedContent) -> None:
    operate_tab = tabbed_content.query_exactly_one(OperateTab)
    op_tab_btn = tabbed_content.get_tab(operate_tab)

    debug_tab = tabbed_content.query_exactly_one(DebugTab)
    debug_tab_btn = tabbed_content.get_tab(debug_tab)

    await _hover_and_click(pilot, op_tab_btn)
    await _set_random_operate_tab_state(pilot, operate_tab)

    await _hover_and_click(pilot, debug_tab_btn)
    await _test_path_operations(pilot, debug_tab)

    await _hover_and_click(pilot, op_tab_btn)
    await _run_operation(pilot, operate_tab)


async def _run_operation(pilot: Pilot[object], op_tab: OperateTab) -> None:
    op_buttons = [
        button for button in op_tab.op_btn_group.query(Button) if not button.disabled
    ]
    if not op_buttons:
        return
    await _hover_and_click(pilot, random.choice(op_buttons))
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
        await _toggle_random_collapsible(pilot, modal)
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


def run_with_pilot(app: ChezmoiGui) -> None:
    app.run(auto_pilot=_run_pilot_mode)


async def _run_pilot_mode(pilot: Pilot[object]) -> None:
    await asyncio.sleep(0.5)
    while isinstance(pilot.app.screen, SplashScreen):
        await asyncio.sleep(CHILL_TIME)
    await pilot.wait_for_scheduled_animations()

    tabbed_content = pilot.app.screen.query_exactly_one(TabbedContent)
    await tabbed_content.wait_for_refresh()

    operate_tab = tabbed_content.query_exactly_one(OperateTab)
    logs_tab = tabbed_content.query_exactly_one(LogsTab)
    config_tab = tabbed_content.query_exactly_one(ConfigTab)
    debug_tab = tabbed_content.query_exactly_one(DebugTab)

    # NOTE: operate tab is mounted last, .query(TabPane) returns in mounted order
    for tab_pane in (operate_tab, logs_tab, config_tab, debug_tab):
        tab = tabbed_content.get_tab(tab_pane)
        if not isinstance(tab_pane, OperateTab):
            await _hover_and_click(pilot, tab)
        await _explore_all_tabs_basic(pilot, tab_pane)

    tree_btn_group = operate_tab.left_side_vertical.query_exactly_one(TreeButtons)
    tree_buttons = {button.label: button for button in tree_btn_group.query(Button)}

    await _set_random_operate_tab_state(pilot, operate_tab)
    await _hover_and_click(pilot, tree_buttons[BtnLabel.dest_dir])
    await _set_random_operate_tab_state(pilot, operate_tab)
    await _hover_and_click(pilot, tree_buttons[BtnLabel.refresh])
    await _hover_and_click(pilot, tree_buttons[BtnLabel.expand])
    await _hover_and_click(pilot, tree_buttons[BtnLabel.collapse])

    cm_theme = pilot.app.theme
    themes = pilot.app.available_themes.items()
    dark_themes = {name for name, theme in themes if theme.dark}
    random_dark = random.choice(list(dark_themes - {cm_theme}))

    for theme_name in [cm_theme, random_dark, cm_theme]:
        pilot.app.theme = theme_name
        await pilot.wait_for_scheduled_animations()
        await _run_op_round(pilot, tabbed_content)

    pilot.app.notify("Pilot mode completed.")
