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
from textual.widgets.tree import TreeNode

from chezmoi_mousse import (
    AppType,
    Chars,
    NodeData,
    PathKind,
    TabName,
    Tcss,
    TreeName,
)
from chezmoi_mousse.shared import CurrentApplyNodeMsg, CurrentReAddNodeMsg

if TYPE_CHECKING:

    from chezmoi_mousse import AppIds, PathDict

__all__ = ["ExpandedTree", "ListTree", "ManagedTree", "TreeBase"]


class TreeBase(Tree[NodeData], AppType):

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded

    def __init__(
        self, ids: "AppIds", *, root_node_data: "NodeData", tree_name: TreeName
    ) -> None:
        self.ids = ids
        super().__init__(
            label="root",
            id=self.ids.tree_id(tree=tree_name),
            classes=Tcss.tree_widget,
            data=root_node_data,
        )
        self.expanded_nodes: list[TreeNode[NodeData]] = []
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
        self.guide_depth: int = 3
        self.show_root: bool = False
        self.border_title = " destDir "
        self.add_class(Tcss.border_title_top)
        self.root.data = self.app.root_node_data

    # def create_root_node_data(self, dest_dir: "Path") -> None:
    #     self.root.data = NodeData(
    #         path=dest_dir, path_kind=PathKind.DIR, found=True, status="F"
    #     )

    # the styling method for the node labels
    def style_label(self, node_data: NodeData) -> Text:
        italic: bool = False if node_data.found else True
        styled = "white"
        if node_data.path_kind == PathKind.FILE:
            if node_data.status == "X":
                styled = "dim"
            elif node_data.status in "ADM":
                styled = Style(
                    color=self.node_colors[node_data.status], italic=italic
                )
            elif node_data.status == " ":
                styled = "white"
        elif node_data.path_kind == PathKind.DIR:
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

    def get_expanded_nodes(self) -> None:
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
        self.expanded_nodes = nodes

    def get_leaves_in(self, tree_node: TreeNode[NodeData]) -> list["Path"]:
        return [
            child.data.path
            for child in tree_node.children
            if child.data is not None and child.data.path_kind == PathKind.FILE
        ]

    def get_dir_nodes_in(self, tree_node: TreeNode[NodeData]) -> list["Path"]:
        return [
            child.data.path
            for child in tree_node.children
            if child.data is not None and child.data.path_kind == PathKind.DIR
        ]

    def create_and_add_node(
        self,
        tree_node: TreeNode[NodeData],
        path: "Path",
        status_code: str,
        path_kind: "PathKind",
    ) -> None:
        if self.ids.canvas_name == TabName.re_add:
            # we now check this early on in the _chezmoi.py module
            found = True
        else:
            found: bool = path.exists()
        node_data = NodeData(
            path=path, path_kind=path_kind, found=found, status=status_code
        )
        node_label: Text = self.style_label(node_data)
        if path_kind == PathKind.FILE:
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
            and leaf.data.path_kind == PathKind.FILE
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

        if self.ids.canvas_name == TabName.apply:
            paths: "PathDict" = (
                (self.app.paths.apply_status_files)
                if flat_list
                else self.app.paths.apply_status_files_in(tree_node.data.path)
            )
        else:
            paths: "PathDict" = (
                (self.app.paths.re_add_status_files)
                if flat_list
                else self.app.paths.re_add_status_files_in(tree_node.data.path)
            )

        for file_path, status_code in paths.items():
            if file_path in self.get_leaves_in(tree_node):
                continue
            self.create_and_add_node(
                tree_node, file_path, status_code, path_kind=PathKind.FILE
            )

    def add_files_without_status_in(
        self, *, tree_node: TreeNode[NodeData], flat_list: bool
    ) -> None:
        if tree_node.data is None:
            self.notify_node_data_is_none(tree_node)
            return
        # Both paths cached in the Chezmoi instance, don't cache this here as
        # we update the cache there after a WriteCmd.

        if self.ids.canvas_name == TabName.apply:
            paths: "PathDict" = (
                (self.app.paths.apply_files_without_status)
                if flat_list
                else self.app.paths.apply_files_without_status_in(
                    tree_node.data.path
                )
            )

        else:
            paths: "PathDict" = (
                (self.app.paths.re_add_files_without_status)
                if flat_list
                else self.app.paths.re_add_files_without_status_in(
                    tree_node.data.path
                )
            )

        for file_path, status_code in paths.items():
            if file_path in self.get_leaves_in(tree_node):
                continue
            self.create_and_add_node(
                tree_node, file_path, status_code, path_kind=PathKind.FILE
            )

    def add_status_dirs_in(self, *, tree_node: TreeNode[NodeData]) -> None:
        if tree_node.data is None:
            self.notify_node_data_is_none(tree_node)
            return

        if self.ids.canvas_name == TabName.apply:
            result: "PathDict" = self.app.paths.apply_status_dirs_in(
                tree_node.data.path
            )
            # Add dirs that contain status files but don't have direct status
            for path in self.app.paths.dirs:
                if (
                    path.parent == tree_node.data.path
                    and path not in result
                    and self.app.paths.has_apply_status_paths_in(path)
                ):
                    result[path] = " "
            dir_paths: "PathDict" = dict(sorted(result.items()))
        else:
            result: "PathDict" = self.app.paths.re_add_status_dirs_in(
                tree_node.data.path
            )
            # Add dirs that contain status files but don't have direct status
            for path in self.app.paths.dirs:
                if (
                    path.parent == tree_node.data.path
                    and path not in result
                    and self.app.paths.has_re_add_status_paths_in(path)
                ):
                    result[path] = " "
            dir_paths: "PathDict" = dict(sorted(result.items()))

        for dir_path, status_code in dir_paths.items():
            if dir_path in self.get_dir_nodes_in(tree_node):
                continue
            self.create_and_add_node(
                tree_node, dir_path, status_code, path_kind=PathKind.DIR
            )

    def add_dirs_without_status_in(
        self, *, tree_node: TreeNode[NodeData]
    ) -> None:
        if tree_node.data is None:
            self.notify_node_data_is_none(tree_node)
            return

        if self.ids.canvas_name == TabName.apply:
            dir_paths: "PathDict" = {
                path: "X"
                for path in self.app.paths.dirs
                if path.parent == tree_node.data.path
                and path not in self.app.paths.apply_status_dirs
                and not self.app.paths.has_apply_status_paths_in(path)
            }
        else:
            dir_paths: "PathDict" = {
                path: "X"
                for path in self.app.paths.dirs
                if path.parent == tree_node.data.path
                and path not in self.app.paths.re_add_status_dirs
                and not self.app.paths.has_re_add_status_paths_in(path)
            }

        for dir_path, status_code in dir_paths.items():
            if dir_path in self.get_dir_nodes_in(tree_node):
                continue
            self.create_and_add_node(
                tree_node, dir_path, status_code, path_kind=PathKind.DIR
            )

    @on(Tree.NodeSelected)
    def send_node_context_message(
        self, event: Tree.NodeSelected[NodeData]
    ) -> None:
        if event.node.data is None:
            self.notify_node_data_is_none(event.node)
            return
        if self.ids.canvas_name == TabName.apply:
            self.post_message(CurrentApplyNodeMsg(event.node.data))
        elif self.ids.canvas_name == TabName.re_add:
            self.post_message(CurrentReAddNodeMsg(event.node.data))

    # 4 methods to provide tab navigation without intaraction with the tree
    def on_key(self, event: Key) -> None:
        if event.key == "tab":
            # Check if we can move down (not at last node)
            if self.cursor_line < self.last_line:
                event.stop()
                self.action_cursor_down()
        elif event.key == "shift+tab":
            # Check if we can move up (not at first node)
            if self.cursor_line > 0:
                event.stop()
                self.action_cursor_up()
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

    def __init__(self, ids: "AppIds") -> None:
        self.ids = ids
        if self.app.root_node_data is None:
            raise ValueError("root_node_data is None in ExpandedTree init")
        super().__init__(
            self.ids,
            root_node_data=self.app.root_node_data,
            tree_name=TreeName.expanded_tree,
        )

    def populate_dest_dir(self) -> None:
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
        if tree_node.data.path_kind == PathKind.DIR:
            self.add_status_dirs_in(tree_node=tree_node)
            self.add_status_files_in(tree_node=tree_node, flat_list=False)
            for child in tree_node.children:
                if (
                    child.data is not None
                    and child.data.path_kind == PathKind.DIR
                ):
                    child.expand()
                    self.expand_all_nodes(child)

    def watch_unchanged(self) -> None:
        self.get_expanded_nodes()
        for tree_node in self.expanded_nodes:
            if self.unchanged:
                self.add_files_without_status_in(
                    tree_node=tree_node, flat_list=False
                )
            else:
                self.remove_files_without_status_in(tree_node=tree_node)


class ListTree(TreeBase):

    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, ids: "AppIds") -> None:
        self.ids = ids
        if self.app.root_node_data is None:
            raise ValueError("root_node_data is None in ListTree init")
        super().__init__(
            self.ids,
            root_node_data=self.app.root_node_data,
            tree_name=TreeName.list_tree,
        )

    def populate_dest_dir(self) -> None:
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

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        if self.app.root_node_data is None:
            raise ValueError("root_node_data is None in ManagedTree init")
        super().__init__(
            self.ids,
            root_node_data=self.app.root_node_data,
            tree_name=TreeName.managed_tree,
        )

    def populate_dest_dir(self) -> None:
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
        self.get_expanded_nodes()
        for node in self.expanded_nodes:
            if self.unchanged:
                self.add_files_without_status_in(
                    tree_node=node, flat_list=False
                )
            else:
                self.remove_files_without_status_in(tree_node=node)
