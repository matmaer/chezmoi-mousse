"""Contains subclassed textual classes shared between the ApplyTab and
ReAddTab."""

from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.containers import Horizontal
from textual.widgets import Button, ContentSwitcher, Switch

from chezmoi_mousse import ContainerName, OperateBtn, Switches, TabBtn, Tcss
from chezmoi_mousse.shared import ContentsView, DiffView, GitLogPath

from .trees import ExpandedTree, ListTree, ManagedTree

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds, NodeData

__all__ = ["TabHorizontal"]


class TabHorizontal(Horizontal):

    def __init__(self, *, ids: "AppIds") -> None:
        super().__init__()

        self.ids = ids
        self.expand_all_state = False
        self.tree_switcher_qid = ids.container_id(
            "#", name=ContainerName.tree_switcher
        )

        # Button id's
        self.destroy_btn_qid = self.ids.button_id(
            "#", btn=OperateBtn.destroy_path
        )
        self.forget_btn_qid = self.ids.button_id(
            "#", btn=OperateBtn.forget_path
        )
        self.list_tab_btn_id = ids.button_id(btn=TabBtn.list)
        self.tree_tab_btn_id = ids.button_id(btn=TabBtn.tree)

    def update_view_path(self, path: Path) -> None:
        contents_view = self.query_one(
            self.ids.logger.contents_q, ContentsView
        )
        contents_view.path = path

        diff_view = self.query_one(self.ids.logger.diff_q, DiffView)
        diff_view.path = path

        git_log_path = self.query_one(
            self.ids.container.git_log_path_q, GitLogPath
        )
        git_log_path.path = path

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
                self.ids.filter.expand_all_q, Switch
            )
            if event.button.id == self.tree_tab_btn_id:
                if self.expand_all_state is True:
                    tree_switcher.current = self.ids.tree.expanded
                else:
                    tree_switcher.current = self.ids.tree.managed
                expand_all_switch.disabled = False
                expand_all_switch.tooltip = Switches.expand_all.enabled_tooltip
            elif event.button.id == self.list_tab_btn_id:
                expand_all_switch.disabled = True
                expand_all_switch.tooltip = (
                    Switches.expand_all.disabled_tooltip
                )
                tree_switcher.current = self.ids.tree.list

    @on(Switch.Changed)
    def handle_tree_filter_switches(self, event: Switch.Changed) -> None:
        if event.switch.id == self.ids.filter.unchanged:
            expanded_tree = self.query_one(
                self.ids.tree.expanded_q, ExpandedTree
            )
            expanded_tree.unchanged = event.value

            list_tree = self.query_one(self.ids.tree.list_q, ListTree)
            list_tree.unchanged = event.value

            managed_tree = self.query_one(self.ids.tree.managed_q, ManagedTree)
            managed_tree.unchanged = event.value

        elif event.switch.id == self.ids.filter.expand_all:
            self.expand_all_state = event.value
            tree_switcher = self.query_one(
                self.tree_switcher_qid, ContentSwitcher
            )
            if event.value is True:
                tree_switcher.current = self.ids.tree.expanded
            else:
                tree_switcher.current = self.ids.tree.managed
