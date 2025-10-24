from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.widgets import ContentSwitcher

from chezmoi_mousse import AppType, AreaName, Tcss, TreeName, ViewName

from .contents_view import ContentsView
from .diff_view import DiffView
from .expanded_tree import ExpandedTree
from .git_log_view import GitLogView
from .list_tree import ListTree
from .managed_tree import ManagedTree

if TYPE_CHECKING:
    from chezmoi_mousse import AppType, CanvasIds

__all__ = ["TreeSwitcher", "ViewSwitcher"]


class TreeSwitcher(ContentSwitcher, AppType):

    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        super().__init__(
            id=self.ids.content_switcher_id(area=AreaName.left),
            initial=self.ids.tree_id(tree=TreeName.managed_tree),
            classes=Tcss.content_switcher_left.name,
        )

    def compose(self) -> ComposeResult:
        yield ManagedTree(ids=self.ids)
        yield ListTree(ids=self.ids)
        yield ExpandedTree(ids=self.ids)

    def on_mount(self) -> None:
        self.border_title = " destDir "
        self.add_class(Tcss.border_title_top.name)


class ViewSwitcher(ContentSwitcher, AppType):
    def __init__(self, *, ids: "CanvasIds", diff_reverse: bool):
        self.ids = ids
        self.reverse = diff_reverse
        super().__init__(
            id=self.ids.content_switcher_id(area=AreaName.right),
            initial=self.ids.view_id(view=ViewName.diff_view),
        )

    def compose(self) -> ComposeResult:
        yield DiffView(ids=self.ids, reverse=self.reverse)
        yield ContentsView(ids=self.ids)
        yield GitLogView(ids=self.ids)
