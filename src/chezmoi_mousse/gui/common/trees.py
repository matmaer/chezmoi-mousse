"""Contains subclassed textual classes shared between the ApplyTab and ReAddTab."""

from pathlib import Path
from typing import TYPE_CHECKING

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
    StatusCode,
    TabName,
    Tcss,
    TreeName,
)

from .messages import CurrentApplyNodeMsg, CurrentReAddNodeMsg

if TYPE_CHECKING:

    from chezmoi_mousse import AppIds, PathDict

__all__ = ["ExpandedTree", "ListTree", "ManagedTree", "TreeBase"]


class TreeBase(Tree[NodeData], AppType):

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded

    unchanged: reactive[bool] = reactive(False, init=False)

    root_node_data: NodeData

    def __init__(self, ids: "AppIds", *, tree_name: TreeName) -> None:
        self.ids = ids
        super().__init__(
            label="root",
            id=self.ids.tree_id(tree=tree_name),
            classes=Tcss.tree_widget,
            data=self.root_node_data,
        )
        self.expanded_nodes: list[TreeNode[NodeData]] = []
        self.visible_nodes: list[TreeNode[NodeData]] = []
        self._initial_render = True
        self._first_focus = True
        self._user_interacted = False

    def on_mount(self) -> None:
        self.node_colors: dict[str, str] = {
            "Dir": self.app.theme_variables["text-primary"],
            StatusCode.Deleted: self.app.theme_variables["text-error"],
            StatusCode.Added: self.app.theme_variables["text-success"],
            StatusCode.Modified: self.app.theme_variables["text-warning"],
            StatusCode.No_Change: self.app.theme_variables["text-secondary"],
            StatusCode.fake_no_status: self.app.theme_variables["secondary-lighten-2"],
        }
        self.guide_depth: int = 3
        self.show_root: bool = False
        self.border_title = " destDir "
        self.add_class(Tcss.border_title_top)
        self.root.data = self.root_node_data

    # the styling method for the node labels
    def style_label(self, node_data: NodeData) -> str:
        italic = " italic" if not node_data.found else ""
        if node_data.path_kind == PathKind.FILE:
            if node_data.status in (StatusCode.No_Change, StatusCode.fake_no_status):
                return f"[dim]{node_data.path.name}[/dim]"
            elif node_data.status in (
                StatusCode.Added,
                StatusCode.Deleted,
                StatusCode.Modified,
            ):
                return (
                    f"[{self.node_colors[node_data.status]}"
                    f"{italic}]{node_data.path.name}[/]"
                )
        elif node_data.path_kind == PathKind.DIR:
            if node_data.status in (
                StatusCode.Added,
                StatusCode.Deleted,
                StatusCode.Modified,
            ):
                return (
                    f"[{self.node_colors[node_data.status]}"
                    f"{italic}]{node_data.path.name}[/]"
                )
            elif node_data.status == StatusCode.No_Change:
                return (
                    f"[{self.node_colors[StatusCode.No_Change]}"
                    f"{italic}]{node_data.path.name}[/]"
                )
            elif node_data.status == StatusCode.fake_no_status:
                return (
                    f"[{self.node_colors[StatusCode.fake_no_status]}"
                    f"{italic}]{node_data.path.name}[/]"
                )
            else:
                return (
                    f"[{self.node_colors['Dir']}" f"{italic}]{node_data.path.name}[/]"
                )

        # Fallback
        return node_data.path.name

    def update_expanded_nodes(self) -> None:
        # Recursively calling collect_nodes to collect expanded nodes
        nodes: list[TreeNode[NodeData]] = [self.root]

        def collect_expanded(
            current_node: TreeNode[NodeData],
        ) -> list[TreeNode[NodeData]]:
            expanded: list[TreeNode[NodeData]] = []
            for child in current_node.children:
                if child.is_expanded:
                    expanded.append(child)
                    expanded.extend(collect_expanded(child))
            return expanded

        nodes.extend(collect_expanded(self.root))
        self.expanded_nodes = nodes

    def update_visible_nodes(self) -> None:
        # Recursively calling collect_visible to collect visible nodes
        nodes: list[TreeNode[NodeData]] = []

        def collect_visible(node: TreeNode[NodeData]):
            nodes.append(node)
            if node.is_expanded:
                for child in node.children:
                    collect_visible(child)

        # Start from root's children since root is not visible
        for child in self.root.children:
            collect_visible(child)

        self.visible_nodes = nodes

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
        node_label: str = self.style_label(node_data)
        if path_kind == PathKind.FILE:
            tree_node.add_leaf(label=node_label, data=node_data)
        else:
            tree_node.add(label=node_label, data=node_data)

    def remove_files_without_status_in(self, *, tree_node: TreeNode[NodeData]) -> None:
        current_unchanged_leaves: list[TreeNode[NodeData]] = [
            leaf
            for leaf in tree_node.children
            if leaf.data is not None
            and leaf.data.path_kind == PathKind.FILE
            and leaf.data.status == StatusCode.fake_no_status
        ]
        for leaf in current_unchanged_leaves:
            leaf.remove()

    def add_status_files_in(self, *, tree_node: TreeNode[NodeData]) -> None:
        if tree_node.data is None:
            raise ValueError("tree_node data is None in add_status_files_in")

        if self.ids.canvas_name == TabName.apply:
            paths: "PathDict" = self.app.paths.apply_status_files_in(
                tree_node.data.path
            )
        else:
            paths: "PathDict" = self.app.paths.re_add_status_files_in(
                tree_node.data.path
            )

        for file_path, status_code in paths.items():
            if file_path in self.get_leaves_in(tree_node):
                continue
            self.create_and_add_node(
                tree_node, file_path, status_code, path_kind=PathKind.FILE
            )

    def add_files_without_status_in(self, *, tree_node: TreeNode[NodeData]) -> None:
        if tree_node.data is None:
            raise ValueError("tree_node data is None in add_files_without_status_in")
        if self.ids.canvas_name == TabName.apply:
            paths: "PathDict" = self.app.paths.apply_files_without_status_in(
                tree_node.data.path
            )
        else:
            paths: "PathDict" = self.app.paths.re_add_files_without_status_in(
                tree_node.data.path
            )

        for file_path, status_code in paths.items():
            if file_path in self.get_leaves_in(tree_node):
                continue
            self.create_and_add_node(
                tree_node, file_path, status_code, path_kind=PathKind.FILE
            )

    def add_status_dirs_in(self, *, tree_node: TreeNode[NodeData]) -> None:
        if tree_node.data is None:
            raise ValueError("tree_node data is None in add_status_dirs_in")
        if self.ids.canvas_name == TabName.apply:
            dir_paths: "PathDict" = self.app.paths.apply_status_dirs_in(
                tree_node.data.path
            )
        else:
            dir_paths: "PathDict" = self.app.paths.re_add_status_dirs_in(
                tree_node.data.path
            )
        for dir_path, status_code in dir_paths.items():
            if dir_path in self.get_dir_nodes_in(tree_node):
                continue
            self.create_and_add_node(
                tree_node, dir_path, status_code, path_kind=PathKind.DIR
            )

    def add_dirs_without_status_in(self, *, tree_node: TreeNode[NodeData]) -> None:
        if tree_node.data is None:
            raise ValueError("tree_node data is None in add_dirs_without_status_in")
        if self.ids.canvas_name == TabName.apply:
            if (
                not (
                    self.app.paths.has_apply_status_paths_in(
                        dir_path=tree_node.data.path
                    )
                )
                and tree_node.data.path not in self.app.paths.apply_dirs
            ):
                return
            dir_paths: "PathDict" = {
                path: self.app.paths.apply_dirs[path].status
                for path in self.app.paths.apply_dirs
                if path.parent == tree_node.data.path
                and self.app.paths.apply_dirs[path].status == StatusCode.fake_no_status
            }
        elif self.ids.canvas_name == TabName.re_add:
            if (
                not (
                    self.app.paths.has_re_add_status_paths_in(
                        dir_path=tree_node.data.path
                    )
                )
                and tree_node.data.path not in self.app.paths.re_add_dirs
            ):
                return
            dir_paths: "PathDict" = {
                path: self.app.paths.re_add_dirs[path].status
                for path in self.app.paths.re_add_dirs
                if path.parent == tree_node.data.path
                and self.app.paths.re_add_dirs[path].status == StatusCode.fake_no_status
            }
        else:
            raise ValueError("Invalid canvas_name in add_dirs_without_status_in")
        for dir_path, status_code in dir_paths.items():
            if dir_path in self.get_dir_nodes_in(tree_node):
                continue
            self.create_and_add_node(
                tree_node, dir_path, status_code, path_kind=PathKind.DIR
            )

    @on(Tree.NodeSelected)
    def send_node_context_message(self, event: Tree.NodeSelected[NodeData]) -> None:
        if event.node.data is None:
            raise ValueError("event.node.data is None in send_node_context")
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

    def __init__(self, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(self.ids, tree_name=TreeName.expanded_tree)

    def populate_dest_dir(self) -> None:
        self.expand_all_nodes(self.root)
        self.update_expanded_nodes()
        self.update_visible_nodes()

    @on(TreeBase.NodeExpanded)
    def add_node_children(self, event: TreeBase.NodeExpanded[NodeData]) -> None:
        self.add_status_dirs_in(tree_node=event.node)
        self.add_status_files_in(tree_node=event.node)
        if self.unchanged:
            self.add_dirs_without_status_in(tree_node=event.node)
            self.add_files_without_status_in(tree_node=event.node)
        self.update_expanded_nodes()
        self.update_visible_nodes()

    @on(Tree.NodeCollapsed)
    def on_node_collapsed(self, event: Tree.NodeCollapsed[NodeData]) -> None:
        self.update_expanded_nodes()
        self.update_visible_nodes()

    def expand_all_nodes(self, tree_node: TreeNode[NodeData]) -> None:
        # Recursively expand all directory nodes
        if tree_node.data is None:
            raise ValueError("tree_node data is None in expand_all_nodes")
        if tree_node.data.path_kind == PathKind.DIR:
            self.add_status_dirs_in(tree_node=tree_node)
            self.add_status_files_in(tree_node=tree_node)
            for child in tree_node.children:
                if child.data is not None and child.data.path_kind == PathKind.DIR:
                    child.expand()
                    self.expand_all_nodes(child)

    def watch_unchanged(self) -> None:
        for tree_node in self.expanded_nodes:
            if self.unchanged:
                self.add_files_without_status_in(tree_node=tree_node)
            else:
                self.remove_files_without_status_in(tree_node=tree_node)


class ListTree(TreeBase):

    def __init__(self, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(self.ids, tree_name=TreeName.list_tree)

    def populate_dest_dir(self) -> None:
        self.add_status_files_in(tree_node=self.root)

    def add_status_files_in(self, *, tree_node: TreeNode[NodeData]) -> None:
        # Override to always use flat list for ListTree
        if tree_node.data is None:
            raise ValueError("tree_node data is None in add_status_files_in")
        if self.ids.canvas_name == TabName.apply:
            paths: "PathDict" = self.app.paths.apply_status_files
        else:
            paths: "PathDict" = self.app.paths.re_add_status_files
        for file_path, status_code in paths.items():
            if file_path in self.get_leaves_in(tree_node):
                continue
            self.create_and_add_node(
                tree_node, file_path, status_code, path_kind=PathKind.FILE
            )

    def add_files_without_status_in(self, *, tree_node: TreeNode[NodeData]) -> None:
        # Override to always use flat list for ListTree
        if tree_node.data is None:
            raise ValueError("tree_node data is None in add_files_without_status_in")
        paths: "PathDict" = self.app.paths.no_status_files

        for file_path, status_code in paths.items():
            if file_path in self.get_leaves_in(tree_node):
                continue
            self.create_and_add_node(
                tree_node, file_path, status_code, path_kind=PathKind.FILE
            )

    def watch_unchanged(self) -> None:
        if self.unchanged is True:
            self.add_files_without_status_in(tree_node=self.root)
        else:
            self.remove_files_without_status_in(tree_node=self.root)


class ManagedTree(TreeBase):

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(self.ids, tree_name=TreeName.managed_tree)

    def populate_dest_dir(self) -> None:
        self.add_status_dirs_in(tree_node=self.root)
        self.add_status_files_in(tree_node=self.root)
        self.update_expanded_nodes()
        self.update_visible_nodes()

    @on(TreeBase.NodeExpanded)
    def update_node_children(self, event: TreeBase.NodeExpanded[NodeData]) -> None:
        self.add_status_dirs_in(tree_node=event.node)
        self.add_status_files_in(tree_node=event.node)
        if self.unchanged:
            self.add_dirs_without_status_in(tree_node=event.node)
            self.add_files_without_status_in(tree_node=event.node)
        self.update_expanded_nodes()
        self.update_visible_nodes()

    @on(Tree.NodeCollapsed)
    def on_node_collapsed(self, event: Tree.NodeCollapsed[NodeData]) -> None:
        self.update_expanded_nodes()
        self.update_visible_nodes()

    def watch_unchanged(self) -> None:
        for node in self.expanded_nodes:
            if self.unchanged:
                self.add_files_without_status_in(tree_node=node)
            else:
                self.remove_files_without_status_in(tree_node=node)
