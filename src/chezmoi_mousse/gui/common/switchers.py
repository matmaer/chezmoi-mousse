"""Contains subclassed textual classes shared between the ApplyTab and ReAddTab."""

from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Button, ContentSwitcher

from chezmoi_mousse import FlatBtnLabel, SubTabLabel, Tcss

from .actionables import TabButtons
from .contents import ContentsView
from .diffs import DiffView
from .git_log import GitLog
from .trees import ListTree, ManagedTree

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["TreeSwitcher", "ViewSwitcher"]


class TreeSwitcher(Container):

    def __init__(self, ids: "AppIds"):
        super().__init__(id=ids.container.left_side, classes=Tcss.tab_left_vertical)
        self.ids = ids

    def compose(self) -> ComposeResult:
        yield TabButtons(self.ids, buttons=(SubTabLabel.tree, SubTabLabel.list))
        with ContentSwitcher(
            id=self.ids.switcher.trees,
            initial=self.ids.tree.managed,
            classes=Tcss.content_switcher_left,
        ):
            yield ManagedTree(self.ids)
            yield ListTree(self.ids)
        yield Button(label=FlatBtnLabel.refresh_tree, classes=Tcss.refresh_button)

    @on(Button.Pressed)
    def switch_view(self, event: Button.Pressed) -> None:
        if event.button.has_class(Tcss.tab_button):
            event.stop()
            view_switcher = self.query_exactly_one(ContentSwitcher)
            if event.button.label == SubTabLabel.tree:
                view_switcher.current = self.ids.tree.managed
            elif event.button.label == SubTabLabel.list:
                view_switcher.current = self.ids.tree.list
            return
        if event.button.has_class(Tcss.refresh_button):
            event.stop()
            managed_tree = self.query_exactly_one(ManagedTree)
            managed_tree.populate_tree()
            list_tree = self.query_exactly_one(ListTree)
            list_tree.populate_tree()


class ViewSwitcher(Container):

    def __init__(self, ids: "AppIds"):
        super().__init__(id=ids.container.right_side)
        self.ids = ids

    def compose(self) -> ComposeResult:
        yield TabButtons(
            self.ids,
            buttons=(SubTabLabel.diff, SubTabLabel.contents, SubTabLabel.git_log),
        )
        with ContentSwitcher(initial=self.ids.container.diff):
            yield DiffView(self.ids)
            yield ContentsView(self.ids)
            yield GitLog(self.ids)

    @on(Button.Pressed, Tcss.tab_button.dot_prefix)
    def switch_view(self, event: Button.Pressed) -> None:
        view_switcher = self.query_exactly_one(ContentSwitcher)
        if event.button.label == SubTabLabel.contents:
            view_switcher.current = self.ids.container.contents
        elif event.button.label == SubTabLabel.diff:
            view_switcher.current = self.ids.container.diff
        elif event.button.label == SubTabLabel.git_log:
            view_switcher.current = self.ids.container.git_log
