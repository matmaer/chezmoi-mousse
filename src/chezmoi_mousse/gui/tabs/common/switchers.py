"""Contains subclassed textual classes shared between the ApplyTab and
ReAddTab."""

from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, ContentSwitcher

from chezmoi_mousse import Tcss
from chezmoi_mousse.shared import GitLogPath, TreeTabButtons, ViewTabButtons

from .contents_view import ContentsView
from .diff_view import DiffView
from .trees import ExpandedTree, ListTree, ManagedTree

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import AppIds

__all__ = ["TreeSwitcher", "ViewSwitcher"]


class TreeSwitcher(Vertical):

    def __init__(self, ids: "AppIds"):
        self.ids = ids
        super().__init__(
            id=self.ids.container.left_side, classes=Tcss.tab_left_vertical
        )

    def compose(self) -> ComposeResult:
        yield TreeTabButtons(ids=self.ids)
        with ContentSwitcher(
            id=self.ids.switcher.trees,
            initial=self.ids.tree.managed,
            classes=Tcss.content_switcher_left,
        ):
            yield ManagedTree(ids=self.ids)
            yield ListTree(ids=self.ids)
            yield ExpandedTree(ids=self.ids)


class ViewSwitcher(Vertical):

    destDir: "Path | None" = None

    def __init__(self, *, ids: "AppIds", diff_reverse: bool):
        self.ids = ids
        self.reverse = diff_reverse
        super().__init__(id=self.ids.container.right_side)

    def compose(self) -> ComposeResult:
        yield ViewTabButtons(ids=self.ids)
        with ContentSwitcher(
            id=self.ids.switcher.views, initial=self.ids.container.diff
        ):
            yield DiffView(ids=self.ids, reverse=self.reverse)
            yield ContentsView(ids=self.ids)
            yield GitLogPath(ids=self.ids)

    @on(Button.Pressed)
    def switch_view(self, event: Button.Pressed) -> None:
        view_switcher = self.query_one(
            self.ids.switcher.views_q, ContentSwitcher
        )
        if event.button.id == self.ids.tab_btn.contents:
            view_switcher.current = self.ids.container.contents
        elif event.button.id == self.ids.tab_btn.diff:
            view_switcher.current = self.ids.container.diff
        elif event.button.id == self.ids.tab_btn.git_log:
            view_switcher.current = self.ids.container.git_log_path
