"""Contains subclassed textual classes shared between the ApplyTab and
ReAddTab."""

from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.containers import Horizontal
from textual.widgets import Button, ContentSwitcher, Switch

from chezmoi_mousse import (
    ContainerName,
    OperateBtn,
    Switches,
    TabBtn,
    Tcss,
    TreeName,
    ViewName,
)
from chezmoi_mousse.shared import ContentsView, DiffView, GitLogView

from .trees import ExpandedTree, ListTree, ManagedTree

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds, NodeData

__all__ = ["TabHorizontal"]


class TabHorizontal(Horizontal):

    def __init__(self, *, ids: "CanvasIds") -> None:
        super().__init__(id=ids.tab_container_id)

        self.ids = ids
        self.expand_all_state = False
        self.tree_switcher_qid = ids.content_switcher_id(
            "#", name=ContainerName.tree_switcher
        )

        # Tree id's
        self.expanded_tree_id = self.ids.tree_id(tree=TreeName.expanded_tree)
        self.expanded_tree_qid = self.ids.tree_id(
            "#", tree=TreeName.expanded_tree
        )
        self.list_tree_id = self.ids.tree_id(tree=TreeName.list_tree)
        self.list_tree_qid = self.ids.tree_id("#", tree=TreeName.list_tree)
        self.managed_tree_id = self.ids.tree_id(tree=TreeName.managed_tree)
        self.managed_tree_qid = self.ids.tree_id(
            "#", tree=TreeName.managed_tree
        )

        # View id's
        self.contents_view_qid = ids.view_id("#", view=ViewName.contents_view)
        self.diff_view_qid = ids.view_id("#", view=ViewName.diff_view)
        self.git_log_view_qid = ids.view_id("#", view=ViewName.git_log_view)

        # Button id's
        self.destroy_btn_qid = self.ids.button_id(
            "#", btn=OperateBtn.destroy_path
        )
        self.forget_btn_qid = self.ids.button_id(
            "#", btn=OperateBtn.forget_path
        )
        self.list_tab_btn_id = ids.button_id(btn=TabBtn.list)
        self.tree_tab_btn_id = ids.button_id(btn=TabBtn.tree)
        # Switch id's
        self.expand_all_switch_id = ids.switch_id(switch=Switches.expand_all)
        self.expand_all_switch_qid = ids.switch_id(
            "#", switch=Switches.expand_all
        )
        self.unchanged_switch_id = self.ids.switch_id(
            switch=Switches.unchanged
        )
        self.unchanged_switch_qid = self.ids.switch_id(
            switch=Switches.unchanged
        )

    def update_view_path(self, path: Path) -> None:
        contents_view = self.query_one(self.contents_view_qid, ContentsView)
        contents_view.path = path

        diff_view = self.query_one(self.diff_view_qid, DiffView)
        diff_view.path = path

        git_log_view = self.query_one(self.git_log_view_qid, GitLogView)
        git_log_view.path = path

    def update_other_buttons(self, node_data: "NodeData") -> None:
        destroy_button = self.query_one(self.destroy_btn_qid, Button)
        destroy_button.label = OperateBtn.destroy_path.label(
            node_data.path_type
        )
        destroy_button.tooltip = (
            OperateBtn.destroy_path.file_tooltip
            if node_data.path_type == "file"
            else OperateBtn.destroy_path.dir_tooltip
        )

        forget_button = self.query_one(self.forget_btn_qid, Button)
        forget_button.label = OperateBtn.forget_path.label(node_data.path_type)
        forget_button.tooltip = (
            OperateBtn.forget_path.file_tooltip
            if node_data.path_type == "file"
            else OperateBtn.forget_path.dir_tooltip
        )

        destroy_button.disabled = False
        forget_button.disabled = False

    @on(Button.Pressed, Tcss.tab_button.value)
    def handle_tab_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id in (self.tree_tab_btn_id, self.list_tab_btn_id):
            # toggle expand all switch enabled disabled state
            tree_switcher = self.query_one(
                self.tree_switcher_qid, ContentSwitcher
            )
            expand_all_switch = self.query_one(
                self.expand_all_switch_qid, Switch
            )
            if event.button.id == self.tree_tab_btn_id:
                if self.expand_all_state is True:
                    tree_switcher.current = self.expanded_tree_id
                else:
                    tree_switcher.current = self.managed_tree_id
                expand_all_switch.disabled = False
                expand_all_switch.tooltip = Switches.expand_all.enabled_tooltip
            elif event.button.id == self.list_tab_btn_id:
                expand_all_switch.disabled = True
                expand_all_switch.tooltip = (
                    Switches.expand_all.disabled_tooltip
                )
                tree_switcher.current = self.list_tree_id

    @on(Switch.Changed)
    def handle_tree_filter_switches(self, event: Switch.Changed) -> None:
        if event.switch.id == self.unchanged_switch_id:
            expanded_tree = self.query_one(
                self.expanded_tree_qid, ExpandedTree
            )
            expanded_tree.unchanged = event.value

            list_tree = self.query_one(self.list_tree_qid, ListTree)
            list_tree.unchanged = event.value

            managed_tree = self.query_one(self.managed_tree_qid, ManagedTree)
            managed_tree.unchanged = event.value

        elif event.switch.id == self.expand_all_switch_id:
            self.expand_all_state = event.value
            tree_switcher = self.query_one(
                self.tree_switcher_qid, ContentSwitcher
            )
            if event.value is True:
                tree_switcher.current = self.expanded_tree_id
            else:
                tree_switcher.current = self.managed_tree_id
