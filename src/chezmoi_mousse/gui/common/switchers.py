from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import ContentSwitcher
from textual.widgets.tree import TreeNode

from chezmoi_mousse import AppType, OpBtnEnum, TabLabel, Tcss

from .actionables import OpButton, TabButton, TabButtons
from .contents import ContentsView
from .diffs import DiffView
from .git_log import GitLogView
from .managed_tree import ManagedTree

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["TreeSwitcher", "ViewSwitcher"]


class TreeSwitcher(Vertical, AppType):

    unchanged: reactive[bool] = reactive(False)
    expand_all: reactive[bool] = reactive(False)

    def __init__(self, ids: "AppIds"):
        super().__init__(id=ids.container.left_side, classes=Tcss.tab_left_vertical)
        self.ids = ids
        self.old_expanded_nodes: list[TreeNode[Path]] = []

    def compose(self) -> ComposeResult:
        yield TabButtons(self.ids, (TabLabel.tree,))
        with ContentSwitcher(
            initial=self.ids.managed_tree, classes=Tcss.tree_content_switcher
        ):
            yield ManagedTree(self.ids)
        yield OpButton(
            btn_enum=OpBtnEnum.refresh_tree,
            btn_id=self.ids.op_btn.refresh_tree,
            app_ids=self.ids,
        )

    def on_mount(self) -> None:
        refresh_btn = self.query_one(self.ids.op_btn.refresh_tree_q, OpButton)
        refresh_btn.remove_class(Tcss.operate_button)
        refresh_btn.add_class(Tcss.refresh_button)
        self.content_switcher = self.query_exactly_one(ContentSwitcher)

    @on(TabButton.Pressed)
    def switch_view(self, event: TabButton.Pressed) -> None:
        if event.button.label == TabLabel.tree:
            self.content_switcher.current = self.ids.managed_tree


class ViewSwitcher(Vertical):

    def __init__(self, ids: "AppIds"):
        super().__init__(id=ids.container.right_side)
        self.ids = ids

    def compose(self) -> ComposeResult:
        yield TabButtons(self.ids, (TabLabel.diff, TabLabel.contents, TabLabel.git_log))
        with ContentSwitcher(initial=self.ids.container.diff):
            yield DiffView(self.ids)
            yield ContentsView(self.ids)
            yield GitLogView(self.ids)

    def on_mount(self) -> None:
        self.view_switcher = self.query_exactly_one(ContentSwitcher)
        self.tab_buttons = self.query_exactly_one(Horizontal)
        self.content_switcher = self.query_exactly_one(ContentSwitcher)

    @on(TabButton.Pressed)
    def switch_view(self, event: TabButton.Pressed) -> None:
        if isinstance(event.button, TabButton):
            event.stop()
            if event.button.label == TabLabel.contents:
                self.content_switcher.current = self.ids.container.contents
            elif event.button.label == TabLabel.diff:
                self.content_switcher.current = self.ids.container.diff
            elif event.button.label == TabLabel.git_log:
                self.content_switcher.current = self.ids.container.git_log
