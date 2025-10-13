from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalGroup
from textual.widgets import ContentSwitcher, Switch

from chezmoi_mousse import (
    AreaName,
    CanvasIds,
    Id,
    Switches,
    TabBtn,
    Tcss,
    TreeName,
    ViewName,
)
from chezmoi_mousse.gui import AppType
from chezmoi_mousse.gui.button_groups import TabBtnHorizontal
from chezmoi_mousse.gui.containers import OperateTabsBase, SwitchSlider
from chezmoi_mousse.gui.directory_tree import FilteredDirTree
from chezmoi_mousse.gui.rich_logs import ContentsView, DiffView
from chezmoi_mousse.gui.tree_widgets import ExpandedTree, FlatTree, ManagedTree
from chezmoi_mousse.gui.widgets import GitLogView

__all__ = ["AddTab", "ApplyTab", "ReAddTab"]


class TreeSwitcher(ContentSwitcher, AppType):

    def __init__(self, canvas_ids: CanvasIds):
        self.canvas_ids = canvas_ids
        super().__init__(
            id=self.canvas_ids.content_switcher_id(area=AreaName.left),
            initial=self.canvas_ids.tree_id(tree=TreeName.managed_tree),
            classes=Tcss.content_switcher_left.name,
        )

    def compose(self) -> ComposeResult:
        yield ManagedTree(canvas_ids=self.canvas_ids)
        yield FlatTree(canvas_ids=self.canvas_ids)
        yield ExpandedTree(canvas_ids=self.canvas_ids)

    def on_mount(self) -> None:
        self.border_title = " destDir "
        self.add_class(Tcss.border_title_top.name)


class ViewSwitcher(ContentSwitcher, AppType):
    def __init__(self, *, canvas_ids: CanvasIds, diff_reverse: bool):
        self.canvas_ids = canvas_ids
        self.reverse = diff_reverse
        super().__init__(
            id=self.canvas_ids.content_switcher_id(area=AreaName.right),
            initial=self.canvas_ids.view_id(view=ViewName.diff_view),
        )

    def compose(self) -> ComposeResult:
        yield DiffView(canvas_ids=self.canvas_ids, reverse=self.reverse)
        yield ContentsView(canvas_ids=self.canvas_ids)
        yield GitLogView(canvas_ids=self.canvas_ids)


class ApplyTab(OperateTabsBase):

    def __init__(self) -> None:
        self.ids = Id.apply_tab
        super().__init__(canvas_ids=self.ids)

    def compose(self) -> ComposeResult:
        with Vertical(
            id=self.ids.tab_vertical_id(area=AreaName.left),
            classes=Tcss.tab_left_vertical.name,
        ):
            yield TabBtnHorizontal(
                canvas_ids=self.canvas_ids,
                buttons=(TabBtn.tree, TabBtn.list),
                area=AreaName.left,
            )
            yield TreeSwitcher(self.ids)
        with Vertical(id=self.ids.tab_vertical_id(area=AreaName.right)):
            yield TabBtnHorizontal(
                canvas_ids=self.ids,
                buttons=(TabBtn.diff, TabBtn.contents, TabBtn.git_log),
                area=AreaName.right,
            )
            yield ViewSwitcher(canvas_ids=self.ids, diff_reverse=False)
        yield SwitchSlider(
            canvas_ids=self.ids,
            switches=(Switches.unchanged, Switches.expand_all),
        )


class ReAddTab(OperateTabsBase):

    def __init__(self) -> None:
        self.ids = Id.re_add_tab
        super().__init__(canvas_ids=self.ids)

    def compose(self) -> ComposeResult:
        with Vertical(
            id=self.ids.tab_vertical_id(area=AreaName.left),
            classes=Tcss.tab_left_vertical.name,
        ):
            yield TabBtnHorizontal(
                canvas_ids=self.canvas_ids,
                buttons=(TabBtn.tree, TabBtn.list),
                area=AreaName.left,
            )
            yield TreeSwitcher(canvas_ids=self.ids)
        with Vertical(id=self.ids.tab_vertical_id(area=AreaName.right)):
            yield TabBtnHorizontal(
                canvas_ids=self.ids,
                buttons=(TabBtn.diff, TabBtn.contents, TabBtn.git_log),
                area=AreaName.right,
            )
            yield ViewSwitcher(canvas_ids=self.ids, diff_reverse=True)
        yield SwitchSlider(
            canvas_ids=self.ids,
            switches=(Switches.unchanged, Switches.expand_all),
        )


class AddTab(OperateTabsBase, AppType):

    def __init__(self) -> None:
        self.ids = Id.add_tab
        super().__init__(canvas_ids=self.ids)

    def compose(self) -> ComposeResult:
        with VerticalGroup(
            id=self.ids.tab_vertical_id(area=AreaName.left),
            classes=Tcss.tab_left_vertical.name,
        ):
            yield FilteredDirTree(
                Path.home(), id=self.ids.tree_id(tree=TreeName.add_tree)
            )
        with Vertical(id=self.ids.tab_vertical_id(area=AreaName.right)):
            yield ContentsView(canvas_ids=self.ids)

        yield SwitchSlider(
            canvas_ids=self.ids,
            switches=(Switches.unmanaged_dirs, Switches.unwanted),
        )

    def on_mount(self) -> None:
        contents_view = self.query_exactly_one(ContentsView)
        contents_view.add_class(Tcss.border_title_top.name)
        contents_view.border_title = " destDir "

        dir_tree = self.query_exactly_one(FilteredDirTree)
        dir_tree.add_class(
            Tcss.dir_tree_widget.name, Tcss.border_title_top.name
        )
        dir_tree.border_title = " destDir "
        dir_tree.show_root = False
        dir_tree.guide_depth = 3

    def on_directory_tree_file_selected(
        self, event: FilteredDirTree.FileSelected
    ) -> None:
        event.stop()

        assert event.node.data is not None
        contents_view = self.query_one(
            self.ids.view_id("#", view=ViewName.contents_view), ContentsView
        )
        contents_view.path = event.node.data.path
        contents_view.border_title = f" {event.node.data.path} "

    @on(FilteredDirTree.DirectorySelected)
    def update_contents_view_and_title(
        self, event: FilteredDirTree.DirectorySelected
    ) -> None:
        event.stop()
        assert event.node.data is not None
        contents_view = self.query_one(
            self.ids.view_id("#", view=ViewName.contents_view), ContentsView
        )
        contents_view.path = event.node.data.path
        contents_view.border_title = f" {event.node.data.path} "

    @on(Switch.Changed)
    def handle_filter_switches(self, event: Switch.Changed) -> None:
        event.stop()
        tree = self.query_one(
            self.ids.tree_id("#", tree=TreeName.add_tree), FilteredDirTree
        )
        if event.switch.id == self.ids.switch_id(
            switch=Switches.unmanaged_dirs.value
        ):
            tree.unmanaged_dirs = event.value
        elif event.switch.id == self.ids.switch_id(
            switch=Switches.unwanted.value
        ):
            tree.unwanted = event.value
        tree.reload()
