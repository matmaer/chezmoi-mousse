"""Contains subclassed textual classes shared between the ApplyTab and
ReAddTab."""

from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, ContentSwitcher

from chezmoi_mousse import ContainerName, TabBtn, Tcss
from chezmoi_mousse.shared import (
    ContentsView,
    DiffView,
    GitLogPath,
    TabButtons,
)

from .trees import ExpandedTree, ListTree, ManagedTree

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import AppIds

__all__ = ["TreeSwitcher", "ViewSwitcher"]


class TreeSwitcher(Vertical):

    def __init__(self, ids: "AppIds"):
        self.ids = ids
        super().__init__(
            id=self.ids.container.left_side,
            classes=Tcss.tab_left_vertical.name,
        )

    def compose(self) -> ComposeResult:
        yield TabButtons(ids=self.ids, buttons=(TabBtn.tree, TabBtn.list))
        with ContentSwitcher(
            id=self.ids.container_id(name=ContainerName.tree_switcher),
            initial=self.ids.tree.managed,
            classes=Tcss.content_switcher_left.name,
        ):
            yield ManagedTree(ids=self.ids)
            yield ListTree(ids=self.ids)
            yield ExpandedTree(ids=self.ids)


class ViewSwitcher(Vertical):

    destDir: "Path | None" = None

    def __init__(self, *, ids: "AppIds", diff_reverse: bool):
        self.ids = ids
        self.contents_tab_btn = ids.button_id(btn=TabBtn.contents)
        self.diff_tab_btn = ids.button_id(btn=TabBtn.diff)
        self.git_log_tab_btn = ids.button_id(btn=TabBtn.git_log_path)
        self.reverse = diff_reverse
        super().__init__(id=self.ids.container.right_side)

    def compose(self) -> ComposeResult:
        yield TabButtons(
            ids=self.ids,
            buttons=(TabBtn.diff, TabBtn.contents, TabBtn.git_log_path),
        )
        with ContentSwitcher(
            id=self.ids.container.view_switcher, initial=self.ids.logger.diff
        ):
            yield DiffView(ids=self.ids, reverse=self.reverse)
            yield ContentsView(ids=self.ids)
            yield GitLogPath(ids=self.ids)

    @on(Button.Pressed)
    def switch_tree(self, event: Button.Pressed) -> None:
        view_switcher = self.query_one(
            self.ids.container.view_switcher_q, ContentSwitcher
        )
        if event.button.id == self.contents_tab_btn:
            view_switcher.current = self.ids.logger.contents
        elif event.button.id == self.diff_tab_btn:
            view_switcher.current = self.ids.logger.diff
        elif event.button.id == self.git_log_tab_btn:
            view_switcher.current = self.ids.container.git_log_path
