from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from rich.style import Style
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalGroup
from textual.events import Key
from textual.reactive import reactive
from textual.widgets import Button, ContentSwitcher, Switch, Tree
from textual.widgets._tree import TOGGLE_STYLE
from textual.widgets.tree import TreeNode

from chezmoi_mousse import (
    AppType,
    AreaName,
    Canvas,
    Chars,
    PaneBtn,
    Switches,
    TabBtn,
    Tcss,
    TreeName,
    ViewName,
)

from .button_groups import TabBtnHorizontal
from .directory_tree import FilteredDirTree
from .messages import TreeNodeSelectedMsg
from .rich_views import ContentsView, DiffView
from .switch_slider import SwitchSlider
from .widgets import GitLogView

if TYPE_CHECKING:
    from chezmoi_mousse import ActiveCanvas, CanvasIds

from typing import TYPE_CHECKING

__all__ = [
    "AddTab",
    "ApplyTab",
    "ExpandedTree",
    "FlatTree",
    "ManagedTree",
    "ReAddTab",
]


@dataclass(slots=True)
class NodeData:
    found: bool
    path: "Path"
    # chezmoi status codes processed: A, D, M, or a space
    # "node status" codes:
    #   X (no status but managed)
    #   F (fake for the root node)
    status: str
    is_leaf: bool


class TreeBase(Tree[NodeData], AppType):

    ICON_NODE = Chars.right_triangle
    ICON_NODE_EXPANDED = Chars.down_triangle

    def __init__(self, ids: "CanvasIds", *, tree_name: TreeName) -> None:
        self.tree_name = tree_name
        self.ids = ids
        self._initial_render = True
        self._first_focus = True
        self._user_interacted = False
        if self.ids.canvas_name == Canvas.apply:
            self.active_canvas: "ActiveCanvas" = Canvas.apply
        else:
            self.active_canvas: "ActiveCanvas" = Canvas.re_add
        super().__init__(
            label="root",
            id=self.ids.tree_id(tree=self.tree_name),
            classes=Tcss.tree_widget.name,
        )

    def on_mount(self) -> None:
        self.node_colors: dict[str, str] = {
            "Dir": self.app.theme_variables["text-primary"],
            "D": self.app.theme_variables["text-error"],
            "A": self.app.theme_variables["text-success"],
            "M": self.app.theme_variables["text-warning"],
            " ": self.app.theme_variables["text-secondary"],
        }
        self.guide_depth: int = 3
        self.show_root: bool = False

    # the styling method for the node labels
    def style_label(self, node_data: NodeData) -> Text:
        italic: bool = False if node_data.found else True
        styled = "white"
        if node_data.is_leaf:
            if node_data.status == "X":
                styled = "dim"
            elif node_data.status in "ADM":
                styled = Style(
                    color=self.node_colors[node_data.status], italic=italic
                )
            elif node_data.status == " ":
                styled = "white"
        elif not node_data.is_leaf:
            if node_data.status in "ADM":
                styled = Style(
                    color=self.node_colors[node_data.status], italic=italic
                )
            elif node_data.status == "X" or node_data.status == " ":
                styled = Style(color=self.node_colors[" "], italic=italic)
            else:
                styled = Style(color=self.node_colors["Dir"], italic=italic)

        return Text(node_data.path.name, style=styled)

    # create node data methods
    def create_node_data(
        self, *, path: "Path", is_leaf: bool, status_code: str
    ) -> NodeData:
        found: bool = path.exists()
        return NodeData(
            path=path, is_leaf=is_leaf, found=found, status=status_code
        )

    # node add/remove methods
    def get_expanded_nodes(self) -> list[TreeNode[NodeData]]:
        # Recursively calling collect_nodes
        nodes: list[TreeNode[NodeData]] = [self.root]

        def collect_nodes(
            current_node: TreeNode[NodeData],
        ) -> list[TreeNode[NodeData]]:
            expanded: list[TreeNode[NodeData]] = []
            for child in current_node.children:
                if child.is_expanded:
                    expanded.append(child)
                    expanded.extend(collect_nodes(child))
            return expanded

        nodes.extend(collect_nodes(self.root))
        return nodes

    def _get_existing_paths(
        self, tree_node: TreeNode[NodeData], is_leaf: bool
    ) -> list["Path"]:
        # get existing nodes (files or dirs based on is_leaf)
        return [
            child.data.path
            for child in tree_node.children
            if child.data is not None and child.data.is_leaf is is_leaf
        ]

    def _create_and_add_node(
        self,
        tree_node: TreeNode[NodeData],
        path: "Path",
        status_code: str,
        is_leaf: bool,
    ) -> None:
        node_data: NodeData = self.create_node_data(
            path=path, is_leaf=is_leaf, status_code=status_code
        )
        node_label: Text = self.style_label(node_data)
        if is_leaf:
            tree_node.add_leaf(label=node_label, data=node_data)
        else:
            tree_node.add(label=node_label, data=node_data)

    def remove_files_without_status_in(
        self, *, tree_node: TreeNode[NodeData]
    ) -> None:
        current_unchanged_leaves: list[TreeNode[NodeData]] = [
            leaf
            for leaf in tree_node.children
            if leaf.data is not None
            and leaf.data.is_leaf is True
            and leaf.data.status == "X"
        ]
        for leaf in current_unchanged_leaves:
            leaf.remove()

    def add_status_files_in(self, *, tree_node: TreeNode[NodeData]) -> None:
        if tree_node.data is None:
            return

        existing_leaves = self._get_existing_paths(tree_node, is_leaf=True)

        if self.tree_name == TreeName.flat_tree:
            status_files = self.app.chezmoi.all_status_files(
                self.active_canvas
            )
        else:
            status_files = self.app.chezmoi.status_files_in(
                self.active_canvas, tree_node.data.path
            )

        for file_path, status_code in status_files.items():
            if file_path in existing_leaves:
                continue
            # Only call exists() in re_add canvas
            if (
                self.active_canvas == PaneBtn.re_add_tab
                and not file_path.exists()
            ):
                continue
            self._create_and_add_node(
                tree_node, file_path, status_code, is_leaf=True
            )

    def add_files_without_status_in(
        self, *, tree_node: TreeNode[NodeData]
    ) -> None:
        if tree_node.data is None:
            return

        existing_leaves = self._get_existing_paths(tree_node, is_leaf=True)
        files_without_status = self.app.chezmoi.files_without_status_in(
            self.active_canvas, tree_node.data.path
        )

        for file_path, status_code in files_without_status.items():
            if file_path in existing_leaves:
                continue
            # Only call exists() in re_add canvas
            if (
                self.active_canvas == PaneBtn.re_add_tab
                and not file_path.exists()
            ):
                continue
            self._create_and_add_node(
                tree_node, file_path, status_code, is_leaf=True
            )

    def add_status_dirs_in(self, *, tree_node: TreeNode[NodeData]) -> None:
        if tree_node.data is None:
            return

        existing_dirs = self._get_existing_paths(tree_node, is_leaf=False)
        dir_paths = self.app.chezmoi.status_dirs_in(
            self.active_canvas, tree_node.data.path
        )

        for dir_path, status_code in dir_paths.items():
            if dir_path in existing_dirs:
                continue
            self._create_and_add_node(
                tree_node, dir_path, status_code, is_leaf=False
            )

    def add_dirs_without_status_in(
        self, *, tree_node: TreeNode[NodeData]
    ) -> None:
        if tree_node.data is None:
            return

        existing_dirs = self._get_existing_paths(tree_node, is_leaf=False)
        dir_paths = self.app.chezmoi.dirs_without_status_in(
            self.active_canvas, tree_node.data.path
        )

        for dir_path, status_code in dir_paths.items():
            if dir_path in existing_dirs:
                continue
            self._create_and_add_node(
                tree_node, dir_path, status_code, is_leaf=False
            )

    def _apply_cursor_style(self, node_label: Text, is_cursor: bool) -> Text:
        """Helper to apply cursor-specific styling to a node label."""
        if not is_cursor:
            return node_label

        current_style = node_label.style
        # Apply bold styling when tree is first focused
        if not self._first_focus and self._initial_render:
            if isinstance(current_style, str):
                cursor_style = Style.parse(current_style) + Style(bold=True)
            else:
                cursor_style = current_style + Style(bold=True)
            return Text(node_label.plain, style=cursor_style)
        # Apply underline styling only after actual user interaction
        elif self._user_interacted:
            if isinstance(current_style, str):
                cursor_style = Style.parse(current_style) + Style(
                    underline=True
                )
            else:
                cursor_style = current_style + Style(underline=True)
            return Text(node_label.plain, style=cursor_style)

        return node_label  # No changes if conditions not met

    def render_label(
        self,
        node: TreeNode[NodeData],
        base_style: Style,
        style: Style,  # needed for valid overriding
    ) -> Text:
        # Get base styling from style_label
        if node.data is None:
            return Text("Node data is None")
        node_label = self.style_label(node.data)

        # Apply cursor styling via helper
        node_label = self._apply_cursor_style(
            node_label, node is self.cursor_node
        )

        if node.allow_expand:
            prefix = (
                (
                    self.ICON_NODE_EXPANDED
                    if node.is_expanded
                    else self.ICON_NODE
                ),
                base_style + TOGGLE_STYLE,
            )
        else:
            prefix = ("", base_style)

        text = Text.assemble(prefix, node_label)
        return text

    @on(Tree.NodeCollapsed)
    def remove_node_children(
        self, event: Tree.NodeCollapsed[NodeData]
    ) -> None:
        event.node.remove_children()

    @on(Tree.NodeSelected)
    def send_node_context_message(
        self, event: Tree.NodeSelected[NodeData]
    ) -> None:
        if event.node == self.root:
            return
        if (
            event.node.parent is not None
            and event.node.parent.data is not None
            and event.node.data is not None
        ):
            self.node_selected_msg = TreeNodeSelectedMsg(
                tree_name=self.tree_name,
                node_data=event.node.data,
                node_parent=event.node.parent.data,
                node_leaves=[
                    child.data
                    for child in event.node.children
                    if child.data is not None and child.data.is_leaf is True
                ],
                node_subdirs=[
                    child.data
                    for child in event.node.children
                    if child.data is not None and child.data.is_leaf is False
                ],
            )
        else:
            return
        self.post_message(self.node_selected_msg)

    # 4 methods to provide tab navigation without intaraction with the tree
    def on_key(self, event: Key) -> None:
        if event.key in ("tab", "shift+tab"):
            return
        self._initial_render = False
        self._user_interacted = True

    def on_click(self) -> None:
        self._initial_render = False
        self._user_interacted = True

    def on_focus(self) -> None:
        if self._first_focus:
            self._first_focus = False
            self.refresh()

    def on_blur(self) -> None:
        if not self._user_interacted and not self._first_focus:
            self._first_focus = True
            self.refresh()


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


class ExpandedTree(TreeBase):

    destDir: reactive["Path | None"] = reactive(None, init=False)
    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(self.ids, tree_name=TreeName.expanded_tree)

    def watch_destDir(self) -> None:
        if self.destDir is None:
            return
        self.root.data = NodeData(
            path=self.destDir, is_leaf=False, found=True, status="F"
        )
        self.expand_all_nodes(self.root)

    @on(TreeBase.NodeExpanded)
    def add_node_children(
        self, event: TreeBase.NodeExpanded[NodeData]
    ) -> None:
        self.add_status_dirs_in(tree_node=event.node)
        self.add_status_files_in(tree_node=event.node)
        if self.unchanged:
            self.add_dirs_without_status_in(tree_node=event.node)
            self.add_files_without_status_in(tree_node=event.node)

    def expand_all_nodes(self, node: TreeNode[NodeData]) -> None:
        # Recursively expand all directory nodes
        assert node.data is not None
        if node.data.is_leaf is False:
            self.add_status_dirs_in(tree_node=node)
            self.add_status_files_in(tree_node=node)
            for child in node.children:
                if child.data is not None and child.data.is_leaf is False:
                    child.expand()
                    self.expand_all_nodes(child)

    def watch_unchanged(self) -> None:
        expanded_nodes = self.get_expanded_nodes()
        for tree_node in expanded_nodes:
            if self.unchanged:
                self.add_files_without_status_in(tree_node=tree_node)
            else:
                self.remove_files_without_status_in(tree_node=tree_node)


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
