from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Button, Switch

from chezmoi_mousse import (
    AreaName,
    Canvas,
    OpBtnTooltip,
    OperateBtn,
    Switches,
    TabBtn,
    Tcss,
    TreeName,
    ViewName,
)

from .contents_view import ContentsView
from .diff_view import DiffView
from .git_log_view import GitLogView
from .operate_msg import CurrentOperatePathMsg, TreeNodeSelectedMsg
from .switchers import TreeSwitcher, ViewSwitcher
from .trees import ExpandedTree, ListTree, ManagedTree

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["TabsBase"]


class TabsBase(Horizontal):

    destDir: "Path | None" = None
    current_path: reactive[Path | None] = reactive(None)

    def __init__(self, *, ids: "CanvasIds") -> None:
        self.ids = ids
        self.contents_tab_btn = ids.button_id(btn=TabBtn.contents)
        self.diff_tab_btn = ids.button_id(btn=TabBtn.diff)
        self.expand_all_state = False
        self.git_log_tab_btn = ids.button_id(btn=TabBtn.git_log_path)
        self.list_tab_btn = ids.button_id(btn=TabBtn.list)
        self.tree_tab_btn = ids.button_id(btn=TabBtn.tree)
        self.tree_switcher_qid = self.ids.content_switcher_id(
            "#", area=AreaName.left
        )
        self.view_switcher_qid = self.ids.content_switcher_id(
            "#", area=AreaName.right
        )
        super().__init__(id=self.ids.tab_container_id)

    def _update_view_path(self) -> None:
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

        # Update Button enabled/Disabled state
        if self.ids.canvas_name == Canvas.apply:
            file_button = self.query_one(
                self.ids.button_id("#", btn=OperateBtn.apply_file), Button
            )
            dir_button = self.query_one(
                self.ids.button_id("#", btn=OperateBtn.apply_dir), Button
            )
        elif self.ids.canvas_name == Canvas.re_add:
            file_button = self.query_one(
                self.ids.button_id("#", btn=OperateBtn.re_add_file), Button
            )
            dir_button = self.query_one(
                self.ids.button_id("#", btn=OperateBtn.re_add_dir), Button
            )
        elif self.ids.canvas_name == Canvas.forget:
            file_button = self.query_one(
                self.ids.button_id("#", btn=OperateBtn.forget_file), Button
            )
            dir_button = self.query_one(
                self.ids.button_id("#", btn=OperateBtn.forget_dir), Button
            )
        elif self.ids.canvas_name == Canvas.destroy:
            file_button = self.query_one(
                self.ids.button_id("#", btn=OperateBtn.destroy_file), Button
            )
            dir_button = self.query_one(
                self.ids.button_id("#", btn=OperateBtn.destroy_dir), Button
            )
        else:
            return
        if event.node_data.is_leaf is True:
            if event.node_data.status != "X":
                dir_button.disabled = True
                dir_button.tooltip = OpBtnTooltip.select_dir
                file_button.disabled = False
                file_button.tooltip = None
            else:
                dir_button.disabled = True
                dir_button.tooltip = OpBtnTooltip.dir_without_status
                file_button.disabled = True
                file_button.tooltip = OpBtnTooltip.file_without_status
        elif not event.node_data.is_leaf:
            if event.node_data.status != "X":
                dir_button.disabled = False
                dir_button.tooltip = None
                file_button.disabled = True
                file_button.tooltip = OpBtnTooltip.select_file
            else:
                dir_button.disabled = True
                dir_button.tooltip = OpBtnTooltip.dir_without_status
                file_button.disabled = True
                file_button.tooltip = OpBtnTooltip.file_without_status

    @on(Button.Pressed, Tcss.tab_button.value)
    def handle_tab_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id in (
            self.contents_tab_btn,
            self.diff_tab_btn,
            self.git_log_tab_btn,
        ):
            view_switcher = self.query_one(
                self.view_switcher_qid, ViewSwitcher
            )
            self._update_view_path()
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
        elif event.button.id in (self.tree_tab_btn, self.list_tab_btn):
            # toggle expand all switch enabled disabled state
            tree_switcher = self.query_one(
                self.tree_switcher_qid, TreeSwitcher
            )
            expand_all_switch = self.query_one(
                self.ids.switch_id("#", switch=Switches.expand_all.value),
                Switch,
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
            elif event.button.id == self.list_tab_btn:
                expand_all_switch.disabled = True
                tree_switcher.current = self.ids.tree_id(
                    tree=TreeName.list_tree
                )

    @on(Switch.Changed)
    def handle_tree_filter_switches(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == self.ids.switch_id(
            switch=Switches.unchanged.value
        ):
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
        elif event.switch.id == self.ids.switch_id(
            switch=Switches.expand_all.value
        ):
            self.expand_all_state = event.value
            tree_switcher = self.query_one(
                self.tree_switcher_qid, TreeSwitcher
            )
            if event.value is True:
                tree_switcher.current = self.ids.tree_id(
                    tree=TreeName.expanded_tree
                )
            else:
                tree_switcher.current = self.ids.tree_id(
                    tree=TreeName.managed_tree
                )

    def watch_current_path(self) -> None:
        if self.current_path is None:
            return
        self.post_message(CurrentOperatePathMsg(self.current_path))
