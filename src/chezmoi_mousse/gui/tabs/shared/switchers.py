from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, ContentSwitcher

from chezmoi_mousse import ContainerName, TabBtn, Tcss, TreeName, ViewName

from ....shared.buttons import TabButtons
from ...shared.contents_view import ContentsView
from ...shared.diff_view import DiffView
from ...shared.git_log_view import GitLogView
from .trees import ExpandedTree, ListTree, ManagedTree

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import CanvasIds

__all__ = ["TreeSwitcher", "ViewSwitcher"]


class TreeSwitcher(Vertical):

    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        super().__init__(
            id=self.ids.tab_vertical_id(name=ContainerName.left_side),
            classes=Tcss.tab_left_vertical.name,
        )

    def compose(self) -> ComposeResult:
        yield TabButtons(ids=self.ids, buttons=(TabBtn.tree, TabBtn.list))
        with ContentSwitcher(
            id=self.ids.content_switcher_id(name=ContainerName.tree_switcher),
            initial=self.ids.tree_id(tree=TreeName.managed_tree),
            classes=Tcss.content_switcher_left.name,
        ):
            yield ManagedTree(ids=self.ids)
            yield ListTree(ids=self.ids)
            yield ExpandedTree(ids=self.ids)


class ViewSwitcher(Vertical):

    destDir: "Path | None" = None

    def __init__(self, *, ids: "CanvasIds", diff_reverse: bool):
        self.ids = ids
        self.contents_tab_btn = ids.button_id(btn=TabBtn.contents)
        self.diff_tab_btn = ids.button_id(btn=TabBtn.diff)
        self.git_log_tab_btn = ids.button_id(btn=TabBtn.git_log_path)
        self.view_switcher_id = self.ids.content_switcher_id(
            name=ContainerName.view_switcher
        )
        self.view_switcher_qid = self.ids.content_switcher_id(
            "#", name=ContainerName.view_switcher
        )
        self.reverse = diff_reverse
        super().__init__(
            id=self.ids.tab_vertical_id(name=ContainerName.right_side)
        )

    def compose(self) -> ComposeResult:
        yield TabButtons(
            ids=self.ids,
            buttons=(TabBtn.diff, TabBtn.contents, TabBtn.git_log_path),
        )
        with ContentSwitcher(
            id=self.view_switcher_id,
            initial=self.ids.view_id(view=ViewName.diff_view),
        ):
            yield DiffView(ids=self.ids, reverse=self.reverse)
            yield ContentsView(ids=self.ids)
            yield GitLogView(ids=self.ids)

    @on(Button.Pressed)
    def switch_tree(self, event: Button.Pressed) -> None:
        view_switcher = self.query_one(self.view_switcher_qid, ContentSwitcher)
        if event.button.id == self.contents_tab_btn:
            view_switcher.current = self.ids.view_id(
                view=ViewName.contents_view
            )
        elif event.button.id == self.diff_tab_btn:
            view_switcher.current = self.ids.view_id(view=ViewName.diff_view)
        elif event.button.id == self.git_log_tab_btn:
            view_switcher.current = self.ids.view_id(
                view=ViewName.git_log_view
            )
