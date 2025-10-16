from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.containers import Horizontal, VerticalGroup
from textual.widgets import Button, ContentSwitcher, Switch

from chezmoi_mousse import AreaName, Switches, TabBtn, Tcss, TreeName, ViewName

from .operate.contents_view import ContentsView
from .operate.diff_view import DiffView
from .operate.expanded_tree import ExpandedTree
from .operate.flat_tree import FlatTree
from .operate.git_log_view import GitLogView
from .operate.managed_tree import ManagedTree
from .operate.operate_msg import TreeNodeSelectedMsg

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["TabsBase"]


class TabsBase(Horizontal):

    def __init__(self, *, ids: "CanvasIds") -> None:
        self.current_path: Path | None = None
        self.ids = ids
        self.diff_tab_btn = ids.button_id(btn=TabBtn.diff)
        self.contents_tab_btn = ids.button_id(btn=TabBtn.contents)
        self.git_log_tab_btn = ids.button_id(btn=TabBtn.git_log)
        self.expand_all_state = False
        self.view_switcher_qid = self.ids.content_switcher_id(
            "#", area=AreaName.right
        )
        self.tree_switcher_qid = self.ids.content_switcher_id(
            "#", area=AreaName.left
        )
        super().__init__(id=self.ids.tab_container_id)

    def _update_view_path(self) -> None:
        if self.current_path is None:
            return
        contents_view = self.query_exactly_one(ContentsView)
        if contents_view.path != self.current_path:
            contents_view.path = self.current_path
            contents_view.border_title = f" {self.current_path} "

        diff_view = self.query_exactly_one(DiffView)
        if diff_view.path != self.current_path:
            diff_view.path = self.current_path
            diff_view.border_title = f" {self.current_path} "

        git_log_view = self.query_exactly_one(GitLogView)
        if git_log_view.path != self.current_path:
            git_log_view.path = self.current_path
            git_log_view.border_title = f" {self.current_path} "

    @on(TreeNodeSelectedMsg)
    def update_current_path(self, event: TreeNodeSelectedMsg) -> None:
        self.current_path = event.node_data.path
        self._update_view_path()

    @on(Button.Pressed, Tcss.tab_button.value)
    def handle_tab_button_pressed(self, event: Button.Pressed) -> None:
        # switch content and update view path if needed
        if event.button.id in (
            self.contents_tab_btn,
            self.diff_tab_btn,
            self.git_log_tab_btn,
        ):
            self._update_view_path()
            view_switcher = self.query_one(
                self.view_switcher_qid, ContentSwitcher
            )
            if event.button.id == self.contents_tab_btn:
                view_switcher.current = self.ids.view_id(
                    view=ViewName.contents_view
                )
            elif event.button.id == self.diff_tab_btn:
                view_switcher.current = self.ids.view_id(
                    view=ViewName.diff_view
                )
            elif event.button.id == self.git_log_tab_btn:
                view_switcher.current = self.ids.view_id(
                    view=ViewName.git_log_view
                )

        # toggle expand all switch enabled disabled state
        expand_all_switch = self.query_one(
            self.ids.switch_id("#", switch=Switches.expand_all.value), Switch
        )
        if event.button.id == self.ids.button_id(btn=TabBtn.tree):
            expand_all_switch.disabled = False
        elif event.button.id == self.ids.button_id(btn=TabBtn.list):
            expand_all_switch.disabled = True

        # switch tree content view
        tree_switcher = self.query_one(self.tree_switcher_qid, ContentSwitcher)
        if event.button.id == self.ids.button_id(btn=TabBtn.tree):
            if self.expand_all_state is True:
                tree_switcher.current = self.ids.tree_id(
                    tree=TreeName.expanded_tree
                )
            else:
                tree_switcher.current = self.ids.tree_id(
                    tree=TreeName.managed_tree
                )
        elif event.button.id == self.ids.button_id(btn=TabBtn.list):
            tree_switcher.current = self.ids.tree_id(tree=TreeName.flat_tree)

    @on(Switch.Changed)
    def handle_tree_filter_switches(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == self.ids.switch_id(
            switch=Switches.unchanged.value
        ):
            tree_pairs: list[
                tuple[TreeName, type[ExpandedTree | ManagedTree | FlatTree]]
            ] = [
                (TreeName.expanded_tree, ExpandedTree),
                (TreeName.managed_tree, ManagedTree),
                (TreeName.flat_tree, FlatTree),
            ]
            for tree_str, tree_cls in tree_pairs:
                self.query_one(
                    self.ids.tree_id("#", tree=tree_str), tree_cls
                ).unchanged = event.value
        elif event.switch.id == self.ids.switch_id(
            switch=Switches.expand_all.value
        ):
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

    def action_toggle_switch_slider(self) -> None:
        self.query_one(
            self.ids.switches_slider_qid, VerticalGroup
        ).toggle_class("-visible")
