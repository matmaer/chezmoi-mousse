from pathlib import Path
from typing import TYPE_CHECKING

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalGroup
from textual.reactive import reactive
from textual.widgets import Button, ContentSwitcher, Switch

from chezmoi_mousse import (
    AppType,
    AreaName,
    Canvas,
    NodeData,
    Switches,
    TabBtn,
    Tcss,
    TreeName,
    ViewName,
)

from .directory_tree import FilteredDirTree
from .shared.button_groups import TabBtnHorizontal
from .shared.expanded_tree import ExpandedTree
from .shared.git_log_view import GitLogView
from .shared.messages import TreeNodeSelectedMsg
from .shared.rich_views import ContentsView, DiffView
from .shared.switch_slider import SwitchSlider
from .shared.tree_base import TreeBase

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = [
    "AddTab",
    "ApplyTab",
    # "ExpandedTree",
    "FlatTree",
    "ManagedTree",
    "ReAddTab",
]


class ManagedTree(TreeBase):

    destDir: reactive["Path | None"] = reactive(None, init=False)
    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, *, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(self.ids, tree_name=TreeName.managed_tree)

    def watch_destDir(self) -> None:
        if self.destDir is None:
            return
        self.root.data = NodeData(
            path=self.destDir, is_leaf=False, found=True, status="F"
        )

        self.add_status_dirs_in(tree_node=self.root)
        self.add_status_files_in(tree_node=self.root)

    @on(TreeBase.NodeExpanded)
    def update_node_children(
        self, event: TreeBase.NodeExpanded[NodeData]
    ) -> None:
        self.add_status_dirs_in(tree_node=event.node)
        self.add_status_files_in(tree_node=event.node)
        if self.unchanged:
            self.add_dirs_without_status_in(tree_node=event.node)
            self.add_files_without_status_in(tree_node=event.node)

    def watch_unchanged(self) -> None:
        for node in self.get_expanded_nodes():
            if self.unchanged:
                self.add_files_without_status_in(tree_node=node)
            else:
                self.remove_files_without_status_in(tree_node=node)


class FlatTree(TreeBase, AppType):

    destDir: reactive["Path | None"] = reactive(None, init=False)
    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, ids: "CanvasIds") -> None:

        super().__init__(ids, tree_name=TreeName.flat_tree)

    def add_files_with_status(self) -> None:
        if self.active_canvas == Canvas.apply:
            status_files = self.app.chezmoi.all_status_files(
                active_canvas=Canvas.apply
            )
        else:
            status_files = self.app.chezmoi.all_status_files(
                active_canvas=Canvas.re_add
            )
        for file_path, status_code in status_files.items():
            node_data: NodeData = self.create_node_data(
                path=file_path, is_leaf=True, status_code=status_code
            )
            if (
                self.active_canvas == Canvas.re_add
                and node_data.found is False
            ):
                continue
            node_label: Text = self.style_label(node_data)
            self.root.add_leaf(label=node_label, data=node_data)

    def watch_destDir(self) -> None:
        if self.destDir is None:
            return
        self.root.data = NodeData(
            path=self.destDir, is_leaf=False, found=True, status="F"
        )
        self.add_files_with_status()

    def watch_unchanged(self) -> None:
        if self.unchanged:
            self.add_files_without_status_in(tree_node=self.root)
        else:
            self.remove_files_without_status_in(tree_node=self.root)


class OperateTabsBase(Horizontal, AppType):

    def __init__(self, *, ids: "CanvasIds") -> None:
        self.current_path: Path | None = None
        self.ids = ids
        self.diff_tab_btn = ids.button_id(btn=TabBtn.diff)
        self.contents_tab_btn = ids.button_id(btn=TabBtn.contents)
        self.git_log_tab_btn = ids.button_id(btn=TabBtn.git_log)
        self.expand_all_state = False
        self.view_switcher_qid = self.ids.content_switcher_id(
            "#", area=AreaName.right
        )
        self.tree_switcher_qid = self.ids.content_switcher_id(
            "#", area=AreaName.left
        )
        super().__init__(id=self.ids.tab_container_id)

    def _update_view_path(self) -> None:
        if self.current_path is None:
            return
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

    @on(Button.Pressed, Tcss.tab_button.value)
    def handle_tab_button_pressed(self, event: Button.Pressed) -> None:
        # switch content and update view path if needed
        if event.button.id in (
            self.contents_tab_btn,
            self.diff_tab_btn,
            self.git_log_tab_btn,
        ):
            self._update_view_path()
            view_switcher = self.query_one(
                self.view_switcher_qid, ContentSwitcher
            )
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

        # toggle expand all switch enabled disabled state
        expand_all_switch = self.query_one(
            self.ids.switch_id("#", switch=Switches.expand_all.value), Switch
        )
        if event.button.id == self.ids.button_id(btn=TabBtn.tree):
            expand_all_switch.disabled = False
        elif event.button.id == self.ids.button_id(btn=TabBtn.list):
            expand_all_switch.disabled = True

        # switch tree content view
        tree_switcher = self.query_one(self.tree_switcher_qid, ContentSwitcher)
        if event.button.id == self.ids.button_id(btn=TabBtn.tree):
            if self.expand_all_state is True:
                tree_switcher.current = self.ids.tree_id(
                    tree=TreeName.expanded_tree
                )
            else:
                tree_switcher.current = self.ids.tree_id(
                    tree=TreeName.managed_tree
                )
        elif event.button.id == self.ids.button_id(btn=TabBtn.list):
            tree_switcher.current = self.ids.tree_id(tree=TreeName.flat_tree)

    @on(Switch.Changed)
    def handle_tree_filter_switches(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == self.ids.switch_id(
            switch=Switches.unchanged.value
        ):
            tree_pairs: list[
                tuple[TreeName, type[ExpandedTree | ManagedTree | FlatTree]]
            ] = [
                (TreeName.expanded_tree, ExpandedTree),
                (TreeName.managed_tree, ManagedTree),
                (TreeName.flat_tree, FlatTree),
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
                self.tree_switcher_qid, ContentSwitcher
            )
            if event.value is True:
                tree_switcher.current = self.ids.tree_id(
                    tree=TreeName.expanded_tree
                )
            else:
                tree_switcher.current = self.ids.tree_id(
                    tree=TreeName.managed_tree
                )

    def action_toggle_switch_slider(self) -> None:
        self.query_one(
            self.ids.switches_slider_qid, VerticalGroup
        ).toggle_class("-visible")


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
        yield FlatTree(ids=self.ids)
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


class ApplyTab(OperateTabsBase):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(ids=self.ids)

    def compose(self) -> ComposeResult:
        with Vertical(
            id=self.ids.tab_vertical_id(area=AreaName.left),
            classes=Tcss.tab_left_vertical.name,
        ):
            yield TabBtnHorizontal(
                ids=self.ids,
                buttons=(TabBtn.tree, TabBtn.list),
                area=AreaName.left,
            )
            yield TreeSwitcher(self.ids)
        with Vertical(id=self.ids.tab_vertical_id(area=AreaName.right)):
            yield TabBtnHorizontal(
                ids=self.ids,
                buttons=(TabBtn.diff, TabBtn.contents, TabBtn.git_log),
                area=AreaName.right,
            )
            yield ViewSwitcher(ids=self.ids, diff_reverse=False)
        yield SwitchSlider(
            ids=self.ids, switches=(Switches.unchanged, Switches.expand_all)
        )


class ReAddTab(OperateTabsBase):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(ids=self.ids)

    def compose(self) -> ComposeResult:
        with Vertical(
            id=self.ids.tab_vertical_id(area=AreaName.left),
            classes=Tcss.tab_left_vertical.name,
        ):
            yield TabBtnHorizontal(
                ids=self.ids,
                buttons=(TabBtn.tree, TabBtn.list),
                area=AreaName.left,
            )
            yield TreeSwitcher(ids=self.ids)
        with Vertical(id=self.ids.tab_vertical_id(area=AreaName.right)):
            yield TabBtnHorizontal(
                ids=self.ids,
                buttons=(TabBtn.diff, TabBtn.contents, TabBtn.git_log),
                area=AreaName.right,
            )
            yield ViewSwitcher(ids=self.ids, diff_reverse=True)
        yield SwitchSlider(
            ids=self.ids, switches=(Switches.unchanged, Switches.expand_all)
        )


class AddTab(OperateTabsBase, AppType):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(ids=self.ids)

    def compose(self) -> ComposeResult:
        with VerticalGroup(
            id=self.ids.tab_vertical_id(area=AreaName.left),
            classes=Tcss.tab_left_vertical.name,
        ):
            yield FilteredDirTree(
                Path.home(), id=self.ids.tree_id(tree=TreeName.add_tree)
            )
        with Vertical(id=self.ids.tab_vertical_id(area=AreaName.right)):
            yield ContentsView(ids=self.ids)

        yield SwitchSlider(
            ids=self.ids, switches=(Switches.unmanaged_dirs, Switches.unwanted)
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
