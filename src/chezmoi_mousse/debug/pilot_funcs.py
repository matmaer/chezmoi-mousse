"""Module for testing the application by interfacing programmatically."""

from __future__ import annotations

import asyncio
import random
from typing import TYPE_CHECKING

from textual.widgets import Button, Collapsible, RadioButton, Switch, Tab
from textual.widgets.collapsible import CollapsibleTitle

from chezmoi_mousse import store
from chezmoi_mousse.gui.operate_tab import OperateTab

if TYPE_CHECKING:
    from textual.pilot import Pilot
    from textual.widget import Widget
    from textual.widgets import TabPane
    from textual.widgets.tree import TreeNode

    from chezmoi_mousse.data_types import NodeData
    from chezmoi_mousse.gui.common.operate_tree import OperateTree

type HoverClickTypes = Button | RadioButton | Switch | CollapsibleTitle | Tab

__all__ = ["NoChill", "WithChill"]

CHILL_TIME = 0.1


async def _chill_sleep(pilot: Pilot[object]) -> None:
    await pilot.wait_for_scheduled_animations()
    await asyncio.sleep(CHILL_TIME)


class NoChill:
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
    async def tree_refresh_wait(pilot: Pilot[object], tree: OperateTree) -> None:
        tree.refresh()
        await tree.wait_for_refresh()
        await pilot.wait_for_scheduled_animations()

    @staticmethod
    async def press_key(pilot: Pilot[object], key: str) -> None:
        await pilot.press(key)
        await pilot.wait_for_scheduled_animations()

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
            if widget.show_vertical_scrollbar:
                widget.scroll_end()
            if widget.show_horizontal_scrollbar:
                while not widget.is_horizontal_scroll_end:
                    widget.scroll_right()
                    await asyncio.sleep(CHILL_TIME / 100)
            widget.scroll_home()
        await pilot.wait_for_scheduled_animations()

    @staticmethod
    async def toggle_bindings(pilot: Pilot[object], tab_pane: TabPane) -> None:
        for key in "CTM":
            if not isinstance(tab_pane, OperateTab) and key in "CT":
                continue
            await NoChill.press_key(pilot, key)
            await NoChill.press_key(pilot, key)

    @staticmethod
    async def click_tree_btn(pilot: Pilot[object], widget: HoverClickTypes) -> None:
        await pilot.click(widget)
        await pilot.wait_for_animation()


class WithChill:
    @staticmethod
    async def hover_and_click(pilot: Pilot[object], widget: HoverClickTypes) -> None:
        if widget.is_on_screen and widget.display:
            if widget.screen.scroll_to_widget(widget):
                await pilot.wait_for_scheduled_animations()
            await pilot.hover(widget)
            await _chill_sleep(pilot)
            await pilot.click(widget)
            await pilot.wait_for_scheduled_animations()

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
    async def select_random_tree_node(pilot: Pilot[object], tree: OperateTree) -> None:
        await NoChill.tree_refresh_wait(pilot, tree)
        cursor_node: TreeNode[NodeData] | None = tree.cursor_node
        child_nodes = {p: n for p, n in tree.node_map.items() if n != tree.root}
        child_paths = list(child_nodes.keys())
        first_node: TreeNode[NodeData] | None = next(iter(child_nodes.values()))
        if not child_nodes or len(child_paths) == 0:
            return
        if len(child_paths) == 1:
            tree.select_node(first_node)
            return
        if len(child_paths) == 2:
            tree.select_node(child_nodes[child_paths[1]])
            return

        if cursor_node is None:
            tree.move_cursor(first_node)
            cursor_node = first_node

        assert cursor_node.data is not None

        choices = [p for p in child_paths if p != cursor_node.data.path]
        random_path = random.choice(choices)

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
