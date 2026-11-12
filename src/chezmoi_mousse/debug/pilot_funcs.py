"""Module for testing the application by interfacing programmatically."""

from __future__ import annotations

import asyncio
import random
from typing import TYPE_CHECKING

from textual.widgets import Button, Collapsible, RadioButton, Switch, Tab
from textual.widgets.collapsible import CollapsibleTitle

from chezmoi_mousse import store
from chezmoi_mousse.gui.common.actionables import SwitchGroup
from chezmoi_mousse.gui.common.operate_tree import OperateTree
from chezmoi_mousse.gui.operate_tab import OperateTab
from chezmoi_mousse.str_enums import BtnLabel

if TYPE_CHECKING:
    from textual.pilot import Pilot
    from textual.widget import Widget
    from textual.widgets import TabPane
    from textual.widgets.tree import TreeNode

    from chezmoi_mousse.data_types import NodeData
    from chezmoi_mousse.gui.common.operate_tree import OperateTree


if TYPE_CHECKING:
    from textual.pilot import Pilot
    from textual.widgets import TabPane
    from textual.widgets.tree import TreeNode

    from chezmoi_mousse.data_types import NodeData
type HoverClickTypes = Button | RadioButton | Switch | CollapsibleTitle | Tab

__all__ = ["NoChill", "WithChill"]

CHILL_TIME = 0.1


async def _chill_sleep(pilot: Pilot[object]) -> None:
    await pilot.wait_for_scheduled_animations()
    await asyncio.sleep(CHILL_TIME)


class NoChill:
    @staticmethod
    async def click_widget(pilot: Pilot[object], widget: HoverClickTypes) -> None:
        if widget.is_on_screen and widget.display:
            if widget.screen.scroll_to_widget(widget):
                await pilot.wait_for_animation()
            await pilot.click(widget)
            await pilot.wait_for_animation()

    @staticmethod
    async def hover_widget(pilot: Pilot[object], widget: HoverClickTypes) -> None:
        if widget.is_on_screen and widget.display:
            if widget.screen.scroll_to_widget(widget):
                await pilot.wait_for_animation()
            await pilot.hover(widget)
            await pilot.wait_for_animation()

    @staticmethod
    async def get_random_collapsible_title(
        root: Widget, *, collapsed: bool
    ) -> CollapsibleTitle | None:
        eligible = [
            w
            for w in root.query(Collapsible).results(Collapsible)
            if w.display and w.is_on_screen and w.collapsed == collapsed
        ]
        if eligible:
            chosen = random.choice(eligible)
            return chosen.query_exactly_one(CollapsibleTitle)

    @staticmethod
    async def get_random_op_btn(op_tab: OperateTab) -> Button | None:
        op_group_buttons = op_tab.op_btn_group.query(Button).results()
        eligible = [
            btn
            for btn in op_group_buttons
            if not btn.disabled and btn.label in BtnLabel.op_btn_labels()
        ]
        if eligible:
            return random.choice(eligible)

    @staticmethod
    async def get_switches(pilot: Pilot[object]) -> list[Switch]:
        switch_group = pilot.app.query_exactly_one(SwitchGroup)
        return list(switch_group.query(Switch).results())

    @staticmethod
    async def reset_operate_switches(pilot: Pilot[object]) -> None:
        switch_group = pilot.app.query_exactly_one(SwitchGroup)
        switch_buttons = list(switch_group.query_children(Switch).results())
        for switch in reversed(switch_buttons):
            if switch.value is True:
                await WithChill.hover_and_click(pilot, switch)
        await pilot.wait_for_scheduled_animations()

    @staticmethod
    async def tree_refresh_wait(pilot: Pilot[object], tree: OperateTree) -> None:
        tree.refresh()
        await tree.wait_for_refresh()
        await pilot.wait_for_animation()

    @staticmethod
    async def press_key(pilot: Pilot[object], key: str) -> None:
        await pilot.press(key)
        await pilot.wait_for_animation()

    @staticmethod
    async def scroll_relevant_widget(pilot: Pilot[object], root: Widget) -> None:
        scrollables = [
            w
            for w in root.query().results()
            if w.is_scrollable
            and w.display
            and w.is_on_screen
            and (w.show_vertical_scrollbar or w.show_horizontal_scrollbar)
        ]
        if scrollables:
            widget = random.choice(scrollables)
            await pilot.wait_for_animation()
            if widget.show_vertical_scrollbar:
                widget.scroll_end()
                await pilot.wait_for_animation()
            if widget.show_horizontal_scrollbar:
                while not widget.is_horizontal_scroll_end:
                    widget.scroll_right()
                    await asyncio.sleep(CHILL_TIME / 100)
                await pilot.wait_for_animation()
            widget.scroll_home()
            await pilot.wait_for_animation()
        await pilot.wait_for_scheduled_animations()

    @staticmethod
    async def toggle_bindings(pilot: Pilot[object], tab_pane: TabPane) -> None:
        for key in "CTM":
            if not isinstance(tab_pane, OperateTab) and key in "CT":
                continue
            await NoChill.press_key(pilot, key)
            await NoChill.press_key(pilot, key)
        await pilot.wait_for_scheduled_animations()

    @staticmethod
    async def click_tree_btn(pilot: Pilot[object], widget: HoverClickTypes) -> None:
        await pilot.click(widget)
        await pilot.wait_for_animation()


class WithChill:
    @staticmethod
    async def hover_and_click(pilot: Pilot[object], widget: HoverClickTypes) -> None:
        await NoChill.hover_widget(pilot, widget)
        await _chill_sleep(pilot)
        await NoChill.click_widget(pilot, widget)
        await _chill_sleep(pilot)

    @staticmethod
    async def toggle_random_collapsible_and_scroll(
        pilot: Pilot[object], root: Widget, *, scroll_probability: float
    ) -> None:
        to_collapse = await NoChill.get_random_collapsible_title(root, collapsed=True)
        to_expand = await NoChill.get_random_collapsible_title(root, collapsed=False)
        for title in to_collapse, to_expand:
            if title is None:
                return
            await WithChill.hover_and_click(pilot, title)
            if random.random() < scroll_probability:
                await NoChill.scroll_relevant_widget(pilot, root)
            await WithChill.hover_and_click(pilot, title)

    @staticmethod
    async def select_random_tree_node(
        pilot: Pilot[object], tree: OperateTree
    ) -> TreeNode[NodeData]:
        tree.focus()
        await NoChill.tree_refresh_wait(pilot, tree)
        cursor_node: TreeNode[NodeData] | None = tree.cursor_node
        child_nodes = {p: n for p, n in tree.node_map.items() if n != tree.root}
        child_paths = list(child_nodes.keys())
        first_node: TreeNode[NodeData] | None = next(iter(child_nodes.values()))
        if not child_nodes or len(child_paths) == 0:
            return tree.root
        if len(child_paths) == 1:
            tree.select_node(first_node)
            return tree.root
        if len(child_paths) == 2:
            tree.select_node(child_nodes[child_paths[1]])
            return tree.root

        if cursor_node is None:
            tree.move_cursor(first_node)
            cursor_node = first_node

        assert cursor_node.data is not None

        choices = {
            p: n
            for p, n in child_nodes.items()
            if p != cursor_node.data.path
            and n.data is not None
            and n.data.filtered is False
        }
        random_path = random.choice(list(choices))
        for parent in [
            par
            for par in reversed(random_path.parents)
            if par.is_relative_to(store.cfg.dest_dir) and par != store.cfg.dest_dir
        ]:
            node = tree.node_map[parent]
            if node != tree.root and node.is_collapsed:
                node.expand()

        await NoChill.tree_refresh_wait(pilot, tree)

        random_node = child_nodes[random_path]
        if tree.cursor_line != random_node.line:
            key = "down" if tree.cursor_line < random_node.line else "up"
            while tree.cursor_node != random_node:
                await NoChill.press_key(pilot, key)

        tree.select_node(random_node)
        await NoChill.tree_refresh_wait(pilot, tree)
        await _chill_sleep(pilot)
        await pilot.wait_for_scheduled_animations()
        return random_node
