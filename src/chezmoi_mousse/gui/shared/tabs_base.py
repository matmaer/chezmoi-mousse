from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.containers import Horizontal
from textual.widgets import Button, ContentSwitcher, Switch

from chezmoi_mousse import (
    OperateBtn,
    SwitcherName,
    Switches,
    TabBtn,
    Tcss,
    TreeName,
    ViewName,
)

from .contents_view import ContentsView
from .diff_view import DiffView
from .git_log_view import GitLogView
from .trees import ExpandedTree, ListTree, ManagedTree

if TYPE_CHECKING:
    from chezmoi_mousse import NodeData

    from .canvas_ids import CanvasIds

__all__ = ["ApplyReAddTabsBase", "TabsBase"]


class TabsBase(Horizontal):

    def __init__(self, *, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.tab_container_id)


class ApplyReAddTabsBase(TabsBase):

    def __init__(self, *, ids: "CanvasIds") -> None:
        self.ids = ids
        self.contents_tab_btn = ids.button_id(btn=TabBtn.contents)
        self.contents_view_qid = ids.view_id("#", view=ViewName.contents_view)
        self.diff_view_qid = ids.view_id("#", view=ViewName.diff_view)
        self.expand_all_state = False
        self.git_log_view_qid = ids.view_id("#", view=ViewName.git_log_view)
        self.list_tab_btn = ids.button_id(btn=TabBtn.list)
        self.tree_tab_btn = ids.button_id(btn=TabBtn.tree)
        self.tree_switcher_qid = ids.content_switcher_id(
            "#", switcher_name=SwitcherName.tree_switcher
        )
        super().__init__(ids=self.ids)

    def update_view_path(self, path: Path) -> None:
        contents_view = self.query_exactly_one(
            self.contents_view_qid, ContentsView
        )
        contents_view.path = path

        diff_view = self.query_exactly_one(self.diff_view_qid, DiffView)
        diff_view.path = path

        git_log_view = self.query_exactly_one(
            self.git_log_view_qid, GitLogView
        )
        git_log_view.path = path

    def update_other_buttons(self, node_data: "NodeData") -> None:
        destroy_button = self.query_one(
            self.ids.button_id("#", btn=OperateBtn.destroy_path), Button
        )
        forget_button = self.query_one(
            self.ids.button_id("#", btn=OperateBtn.forget_path), Button
        )
        destroy_button.label = (
            OperateBtn.destroy_path.file_label
            if node_data.path_type == "file"
            else OperateBtn.destroy_path.dir_label
        )
        destroy_button.tooltip = (
            OperateBtn.destroy_path.file_tooltip
            if node_data.path_type == "file"
            else OperateBtn.destroy_path.dir_tooltip
        )
        forget_button.label = (
            OperateBtn.forget_path.file_label
            if node_data.path_type == "file"
            else OperateBtn.forget_path.dir_label
        )
        forget_button.tooltip = (
            OperateBtn.forget_path.file_tooltip
            if node_data.path_type == "file"
            else OperateBtn.forget_path.dir_tooltip
        )

        destroy_button.disabled = False
        forget_button.disabled = False

    @on(Button.Pressed, Tcss.tab_button.value)
    def handle_tab_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id in (self.tree_tab_btn, self.list_tab_btn):
            # toggle expand all switch enabled disabled state
            tree_switcher = self.query_one(
                self.tree_switcher_qid, ContentSwitcher
            )
            expand_all_switch = self.query_one(
                self.ids.switch_id("#", switch=Switches.expand_all), Switch
            )
            if event.button.id == self.tree_tab_btn:
                if self.expand_all_state is True:
                    tree_switcher.current = self.ids.tree_id(
                        tree=TreeName.expanded_tree
                    )
                else:
                    tree_switcher.current = self.ids.tree_id(
                        tree=TreeName.managed_tree
                    )
                expand_all_switch.disabled = False
                expand_all_switch.tooltip = Switches.expand_all.enabled_tooltip
            elif event.button.id == self.list_tab_btn:
                expand_all_switch.disabled = True
                expand_all_switch.tooltip = (
                    Switches.expand_all.disabled_tooltip
                )
                tree_switcher.current = self.ids.tree_id(
                    tree=TreeName.list_tree
                )

    @on(Switch.Changed)
    def handle_tree_filter_switches(self, event: Switch.Changed) -> None:
        if event.switch.id == self.ids.switch_id(switch=Switches.unchanged):
            tree_pairs: list[
                tuple[TreeName, type[ExpandedTree | ManagedTree | ListTree]]
            ] = [
                (TreeName.expanded_tree, ExpandedTree),
                (TreeName.managed_tree, ManagedTree),
                (TreeName.list_tree, ListTree),
            ]
            for tree_str, tree_cls in tree_pairs:
                self.query_one(
                    self.ids.tree_id("#", tree=tree_str), tree_cls
                ).unchanged = event.value
        elif event.switch.id == self.ids.switch_id(switch=Switches.expand_all):
            self.expand_all_state = event.value
            tree_switcher = self.query_one(
                self.tree_switcher_qid, ContentSwitcher
            )
            if event.value is True:
                tree_switcher.current = self.ids.tree_id(
                    tree=TreeName.expanded_tree
                )
            else:
                tree_switcher.current = self.ids.tree_id(
                    tree=TreeName.managed_tree
                )
