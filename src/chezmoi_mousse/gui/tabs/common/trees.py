"""Contains subclassed textual classes shared between the ApplyTab and
ReAddTab."""

from pathlib import Path
from typing import TYPE_CHECKING

from rich.style import Style
from rich.text import Text
from textual import on
from textual.events import Key
from textual.reactive import reactive
from textual.widgets import Tree
from textual.widgets._tree import TOGGLE_STYLE
from textual.widgets.tree import TreeNode

from chezmoi_mousse import (
    AppType,
    CanvasName,
    Chars,
    NodeData,
    PathType,
    Tcss,
    TreeName,
)
from chezmoi_mousse.shared import CurrentApplyNodeMsg, CurrentReAddNodeMsg

if TYPE_CHECKING:

    from chezmoi_mousse import CanvasIds, PathDict

__all__ = ["ExpandedTree", "ListTree", "ManagedTree", "TreeBase"]


class TreeBase(Tree[NodeData], AppType):

    destDir: "Path"

    ICON_NODE = Chars.right_triangle
    ICON_NODE_EXPANDED = Chars.down_triangle

    def __init__(self, ids: "CanvasIds", *, tree_name: TreeName) -> None:
        super().__init__(
            label="root",
            id=ids.tree_id(tree=tree_name),
            classes=Tcss.tree_widget.name,
        )
        self.ids = ids
        self._initial_render = True
        self._first_focus = True
        self._user_interacted = False

    def on_mount(self) -> None:
        self.node_colors: dict[str, str] = {
            "Dir": self.app.theme_variables["text-primary"],
            "D": self.app.theme_variables["text-error"],
            "A": self.app.theme_variables["text-success"],
            "M": self.app.theme_variables["text-warning"],
            " ": self.app.theme_variables["text-secondary"],
        }
        self.root.data = NodeData(
            path=self.destDir, path_type=PathType.DIR, found=True, status="F"
        )
        self.guide_depth: int = 3
        self.show_root: bool = False

    # the styling method for the node labels
    def __style_label(self, node_data: NodeData) -> Text:
        italic: bool = False if node_data.found else True
        styled = "white"
        if node_data.path_type == "file":
            if node_data.status == "X":
                styled = "dim"
            elif node_data.status in "ADM":
                styled = Style(
                    color=self.node_colors[node_data.status], italic=italic
                )
            elif node_data.status == " ":
                styled = "white"
        elif node_data.path_type == "dir":
            if node_data.status in "ADM":
                styled = Style(
                    color=self.node_colors[node_data.status], italic=italic
                )
            elif node_data.status == "X" or node_data.status == " ":
                styled = Style(color=self.node_colors[" "], italic=italic)
            else:
                styled = Style(color=self.node_colors["Dir"], italic=italic)

        return Text(node_data.path.name, style=styled)

    def notify_node_data_is_none(self, tree_node: TreeNode[NodeData]) -> None:
        self.app.notify(
            f"TreeNode data is None for {tree_node.label}", severity="error"
        )

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

    def get_leaves_in(self, tree_node: TreeNode[NodeData]) -> list["Path"]:
        return [
            child.data.path
            for child in tree_node.children
            if child.data is not None and child.data.path_type == "file"
        ]

    def get_dir_nodes_in(self, tree_node: TreeNode[NodeData]) -> list["Path"]:
        return [
            child.data.path
            for child in tree_node.children
            if child.data is not None and child.data.path_type == "dir"
        ]

    def create_and_add_node(
        self,
        tree_node: TreeNode[NodeData],
        path: "Path",
        status_code: str,
        path_type: "PathType",
    ) -> None:
        if self.ids.canvas_name == CanvasName.re_add_tab:
            # we now check this early on in the _chezmoi.py module
            found = True
        else:
            found: bool = path.exists()
        node_data = NodeData(
            path=path, path_type=path_type, found=found, status=status_code
        )
        node_label: Text = self.__style_label(node_data)
        if path_type == "file":
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
            and leaf.data.path_type == "file"
            and leaf.data.status == "X"
        ]
        for leaf in current_unchanged_leaves:
            leaf.remove()

    def add_status_files_in(
        self, *, tree_node: TreeNode[NodeData], flat_list: bool
    ) -> None:
        if tree_node.data is None:
            self.notify_node_data_is_none(tree_node)
            return

        if self.ids.canvas_name == CanvasName.apply_tab:
            paths: "PathDict" = (
                (self.app.chezmoi.apply_status_files)
                if flat_list
                else self.app.chezmoi.apply_status_files_in(
                    tree_node.data.path
                )
            )
        else:
            paths: "PathDict" = (
                (self.app.chezmoi.re_add_status_files)
                if flat_list
                else self.app.chezmoi.re_add_status_files_in(
                    tree_node.data.path
                )
            )

        for file_path, status_code in paths.items():
            if file_path in self.get_leaves_in(tree_node):
                continue
            self.create_and_add_node(
                tree_node, file_path, status_code, path_type=PathType.FILE
            )

    def add_files_without_status_in(
        self, *, tree_node: TreeNode[NodeData], flat_list: bool
    ) -> None:
        if tree_node.data is None:
            self.notify_node_data_is_none(tree_node)
            return
        # Both paths cached in the Chezmoi instance, don't cache this here as
        # we update the cache there after a WriteCmd.

        if self.ids.canvas_name == CanvasName.apply_tab:
            paths: "PathDict" = (
                (self.app.chezmoi.apply_files_without_status)
                if flat_list
                else self.app.chezmoi.apply_files_without_status_in(
                    tree_node.data.path
                )
            )

        else:
            paths: "PathDict" = (
                (self.app.chezmoi.re_add_files_without_status)
                if flat_list
                else self.app.chezmoi.re_add_files_without_status_in(
                    tree_node.data.path
                )
            )

        for file_path, status_code in paths.items():
            if file_path in self.get_leaves_in(tree_node):
                continue
            self.create_and_add_node(
                tree_node, file_path, status_code, path_type=PathType.FILE
            )

    def add_status_dirs_in(self, *, tree_node: TreeNode[NodeData]) -> None:
        if tree_node.data is None:
            self.notify_node_data_is_none(tree_node)
            return

        if self.ids.canvas_name == CanvasName.apply_tab:
            result: "PathDict" = self.app.chezmoi.apply_status_dirs_in(
                tree_node.data.path
            )
            # Add dirs that contain status files but don't have direct status
            for path in self.app.chezmoi.dirs:
                if (
                    path.parent == tree_node.data.path
                    and path not in result
                    and self.app.chezmoi.has_apply_status_paths_in(path)
                ):
                    result[path] = " "
            dir_paths: "PathDict" = dict(sorted(result.items()))
        else:
            result: "PathDict" = self.app.chezmoi.re_add_status_dirs_in(
                tree_node.data.path
            )
            # Add dirs that contain status files but don't have direct status
            for path in self.app.chezmoi.dirs:
                if (
                    path.parent == tree_node.data.path
                    and path not in result
                    and self.app.chezmoi.has_re_add_status_paths_in(path)
                ):
                    result[path] = " "
            dir_paths: "PathDict" = dict(sorted(result.items()))

        for dir_path, status_code in dir_paths.items():
            if dir_path in self.get_dir_nodes_in(tree_node):
                continue
            self.create_and_add_node(
                tree_node, dir_path, status_code, path_type=PathType.DIR
            )

    def add_dirs_without_status_in(
        self, *, tree_node: TreeNode[NodeData]
    ) -> None:
        if tree_node.data is None:
            self.notify_node_data_is_none(tree_node)
            return

        if self.ids.canvas_name == CanvasName.apply_tab:
            dir_paths: "PathDict" = {
                path: "X"
                for path in self.app.chezmoi.dirs
                if path.parent == tree_node.data.path
                and path not in self.app.chezmoi.apply_status_dirs
                and not self.app.chezmoi.has_apply_status_paths_in(path)
            }
        else:
            dir_paths: "PathDict" = {
                path: "X"
                for path in self.app.chezmoi.dirs
                if path.parent == tree_node.data.path
                and path not in self.app.chezmoi.re_add_status_dirs
                and not self.app.chezmoi.has_re_add_status_paths_in(path)
            }

        for dir_path, status_code in dir_paths.items():
            if dir_path in self.get_dir_nodes_in(tree_node):
                continue
            self.create_and_add_node(
                tree_node, dir_path, status_code, path_type=PathType.DIR
            )

    def __apply_cursor_style(self, node_label: Text, is_cursor: bool) -> Text:
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
        node_label = self.__style_label(node.data)

        # Apply cursor styling via helper
        node_label = self.__apply_cursor_style(
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

    @on(Tree.NodeSelected)
    def send_node_context_message(
        self, event: Tree.NodeSelected[NodeData]
    ) -> None:
        if event.node.data is None:
            self.notify_node_data_is_none(event.node)
            return
        if self.ids.canvas_name == CanvasName.apply_tab:
            self.post_message(CurrentApplyNodeMsg(event.node.data))
        elif self.ids.canvas_name == CanvasName.re_add_tab:
            self.post_message(CurrentReAddNodeMsg(event.node.data))

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


class ExpandedTree(TreeBase):

    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(self.ids, tree_name=TreeName.expanded_tree)

    def on_mount(self) -> None:
        self.border_title = " destDir "
        self.add_class(Tcss.border_title_top.name)

    def populate_tree(self) -> None:
        self.clear()
        self.expand_all_nodes(self.root)

    @on(TreeBase.NodeExpanded)
    def add_node_children(
        self, event: TreeBase.NodeExpanded[NodeData]
    ) -> None:
        self.add_status_dirs_in(tree_node=event.node)
        self.add_status_files_in(tree_node=event.node, flat_list=False)
        if self.unchanged:
            self.add_dirs_without_status_in(tree_node=event.node)
            self.add_files_without_status_in(
                tree_node=event.node, flat_list=False
            )

    def expand_all_nodes(self, tree_node: TreeNode[NodeData]) -> None:
        # Recursively expand all directory nodes
        if tree_node.data is None:
            self.notify_node_data_is_none(tree_node)
            return
        if tree_node.data.path_type == "dir":
            self.add_status_dirs_in(tree_node=tree_node)
            self.add_status_files_in(tree_node=tree_node, flat_list=False)
            for child in tree_node.children:
                if child.data is not None and child.data.path_type == "dir":
                    child.expand()
                    self.expand_all_nodes(child)

    def watch_unchanged(self) -> None:
        expanded_nodes = self.get_expanded_nodes()
        for tree_node in expanded_nodes:
            if self.unchanged:
                self.add_files_without_status_in(
                    tree_node=tree_node, flat_list=False
                )
            else:
                self.remove_files_without_status_in(tree_node=tree_node)


class ListTree(TreeBase):

    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(self.ids, tree_name=TreeName.list_tree)

    def on_mount(self) -> None:
        self.border_title = " destDir "
        self.add_class(Tcss.border_title_top.name)

    def populate_tree(self) -> None:
        self.clear()
        self.add_status_files_in(tree_node=self.root, flat_list=True)

    def watch_unchanged(self) -> None:
        if self.unchanged is True:
            self.add_files_without_status_in(
                tree_node=self.root, flat_list=True
            )
        else:
            self.remove_files_without_status_in(tree_node=self.root)


class ManagedTree(TreeBase):

    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, *, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(self.ids, tree_name=TreeName.managed_tree)

    def on_mount(self) -> None:
        self.border_title = " destDir "
        self.add_class(Tcss.border_title_top.name)

    def populate_tree(self) -> None:
        self.clear()
        self.add_status_dirs_in(tree_node=self.root)
        self.add_status_files_in(tree_node=self.root, flat_list=False)

    @on(TreeBase.NodeExpanded)
    def update_node_children(
        self, event: TreeBase.NodeExpanded[NodeData]
    ) -> None:
        self.add_status_dirs_in(tree_node=event.node)
        self.add_status_files_in(tree_node=event.node, flat_list=False)
        if self.unchanged:
            self.add_dirs_without_status_in(tree_node=event.node)
            self.add_files_without_status_in(
                tree_node=event.node, flat_list=False
            )

    def watch_unchanged(self) -> None:
        for node in self.get_expanded_nodes():
            if self.unchanged:
                self.add_files_without_status_in(
                    tree_node=node, flat_list=False
                )
            else:
                self.remove_files_without_status_in(tree_node=node)
