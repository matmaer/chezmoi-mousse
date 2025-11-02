from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import ContentSwitcher

from chezmoi_mousse import AreaName, TabBtn, Tcss, TreeName, ViewName
from chezmoi_mousse.gui.shared.button_groups import TabBtnHorizontal

from .contents_view import ContentsView
from .diff_view import DiffView
from .git_log_view import GitLogView
from .trees import ExpandedTree, ListTree, ManagedTree

if TYPE_CHECKING:
    from .canvas_ids import CanvasIds

__all__ = ["TreeSwitcher", "ViewSwitcher"]


class TreeSwitcher(Vertical):

    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        super().__init__(
            id=self.ids.tab_vertical_id(area=AreaName.left),
            classes=Tcss.tab_left_vertical.name,
        )

    def compose(self) -> ComposeResult:
        yield TabBtnHorizontal(
            ids=self.ids,
            buttons=(TabBtn.tree, TabBtn.list),
            area=AreaName.left,
        )
        with ContentSwitcher(
            id=self.ids.content_switcher_id(area=AreaName.left),
            initial=self.ids.tree_id(tree=TreeName.managed_tree),
            classes=Tcss.content_switcher_left.name,
        ):
            yield ManagedTree(ids=self.ids)
            yield ListTree(ids=self.ids)
            yield ExpandedTree(ids=self.ids)


class ViewSwitcher(Vertical):
    def __init__(self, *, ids: "CanvasIds", diff_reverse: bool):
        self.ids = ids
        self.reverse = diff_reverse
        super().__init__(id=self.ids.tab_vertical_id(area=AreaName.right))

    def compose(self) -> ComposeResult:
        yield TabBtnHorizontal(
            ids=self.ids,
            buttons=(TabBtn.diff, TabBtn.contents, TabBtn.git_log_path),
            area=AreaName.right,
        )
        with ContentSwitcher(
            id=self.ids.content_switcher_id(area=AreaName.right),
            initial=self.ids.view_id(view=ViewName.diff_view),
        ):
            yield DiffView(ids=self.ids, reverse=self.reverse)
            yield ContentsView(ids=self.ids)
            yield GitLogView(ids=self.ids)
