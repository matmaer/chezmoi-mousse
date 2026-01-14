"""Contains subclassed textual classes shared between the ApplyTab and ReAddTab."""

from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, ContentSwitcher

from chezmoi_mousse import SubTabLabel, Tcss

from .actionables import TabButtons
from .trees import ListTree, ManagedTree
from .views import ContentsView, DiffView, GitLogPath

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["TreeSwitcher", "ViewSwitcher"]


class TreeSwitcher(Vertical):

    def __init__(self, ids: "AppIds"):
        self.ids = ids
        super().__init__(
            id=self.ids.container.left_side, classes=Tcss.tab_left_vertical
        )

    def compose(self) -> ComposeResult:
        yield TabButtons(ids=self.ids, buttons=(SubTabLabel.tree, SubTabLabel.list))
        with ContentSwitcher(
            id=self.ids.switcher.trees,
            initial=self.ids.tree.managed,
            classes=Tcss.content_switcher_left,
        ):
            yield ManagedTree(ids=self.ids)
            yield ListTree(ids=self.ids)


class ViewSwitcher(Vertical):

    def __init__(self, *, ids: "AppIds"):
        self.ids = ids
        super().__init__(id=self.ids.container.right_side)

    def compose(self) -> ComposeResult:
        yield TabButtons(
            ids=self.ids,
            buttons=(SubTabLabel.diff, SubTabLabel.contents, SubTabLabel.git_log_path),
        )
        with ContentSwitcher(initial=self.ids.container.diff):
            yield DiffView(ids=self.ids)
            yield ContentsView(ids=self.ids)
            yield GitLogPath(ids=self.ids)

    @on(Button.Pressed, Tcss.tab_button.dot_prefix)
    def switch_view(self, event: Button.Pressed) -> None:
        view_switcher = self.query_exactly_one(ContentSwitcher)
        if event.button.label == SubTabLabel.contents:
            view_switcher.current = self.ids.container.contents
        elif event.button.label == SubTabLabel.diff:
            view_switcher.current = self.ids.container.diff
        elif event.button.label == SubTabLabel.git_log_path:
            view_switcher.current = self.ids.container.git_log_path
