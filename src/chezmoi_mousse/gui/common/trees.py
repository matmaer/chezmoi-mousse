"""Contains subclassed textual classes shared between the ApplyTab and ReAddTab."""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.reactive import reactive
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from chezmoi_mousse import AppType, Chars, PathKind, StatusCode, TabName, Tcss, TreeName

from .messages import CurrentApplyNodeMsg, CurrentReAddNodeMsg

if TYPE_CHECKING:

    from chezmoi_mousse import AppIds

type NodeDict = dict[Path, NodeData]

__all__ = ["ExpandedTree", "ListTree", "ManagedTree", "TreeBase", "NodeData"]


@dataclass(slots=True)
class NodeData:
    found: bool
    path: Path
    status: StatusCode
    path_kind: PathKind


class TreeBase(Tree[NodeData], AppType):

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded

    unchanged: reactive[bool] = reactive(False, init=False)

    root_node_data: NodeData

    def __init__(self, ids: "AppIds", *, tree_name: TreeName) -> None:
        super().__init__(
            label="root",
            id=ids.tree_id(tree=tree_name),
            classes=Tcss.tree_widget,
            data=self.root_node_data,
        )
        self.ids = ids
        self.paths: NodeDict = {}
        self.expanded_nodes: list[TreeNode[NodeData]] = []
        self.visible_nodes: list[TreeNode[NodeData]] = []
        self.paths: NodeDict = {}

    def on_mount(self) -> None:
        self.node_colors: dict[str, str] = {
            StatusCode.Added: self.app.theme_variables["text-success"],
            StatusCode.Deleted: self.app.theme_variables["text-error"],
            StatusCode.Modified: self.app.theme_variables["text-warning"],
            StatusCode.No_Change: self.app.theme_variables["warning-darken-2"],
            # Fake status codes, root and unmanaged are never shown in Tree widgets but
            # allows to simplify the create_and_add_node method.
            StatusCode.root_node: self.app.theme_variables["error"],
            StatusCode.unmanaged: self.app.theme_variables["error-darken-2"],
            StatusCode.file_no_status: self.app.theme_variables["foreground-darken-3"],
            StatusCode.dir_no_status: self.app.theme_variables["foreground-darken-2"],
            StatusCode.dir_with_status_children: self.app.theme_variables[
                "text-primary"
            ],
        }
        self.guide_depth: int = 3
        self.show_root: bool = False
        self.border_title = " destDir "
        self.add_class(Tcss.border_title_top)
        self.root.data = self.root_node_data
        if self.app.dest_dir is None:
            raise ValueError("self.app.dest_dir is None")
        self.paths[self.app.dest_dir] = self.root_node_data
        self.populate_paths()

    def populate_paths(self) -> None:
        for path, path_node in self.app.managed.path_nodes.items():
            status_code = (
                path_node.status_pair[1]
                if self.ids.canvas_name == TabName.apply
                else path_node.status_pair[0]
            )
            self.paths[path] = NodeData(
                found=path_node.found,
                path_kind=path_node.path_kind,
                path=path_node.path,
                status=status_code,
            )

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

    def create_and_add_node(
        self, *, node_data: NodeData, tree_node: TreeNode[NodeData]
    ) -> None:
        italic = " italic" if not node_data.found else ""
        color = self.node_colors[node_data.status]
        node_label = f"[{color}" f"{italic}]{node_data.path.name}[/]"
        if node_data.path_kind == PathKind.FILE:
            tree_node.add_leaf(label=node_label, data=node_data)
        else:
            tree_node.add(label=node_label, data=node_data)

    def create_all_nodes(self) -> None:
        if self.root.data is None:
            raise ValueError(f"self.root.data is None in {self.name}")
        # Create nodes from self.paths (which already has correct status values)
        # Sort by depth to ensure parents are created before children
        path_to_node: dict[Path, TreeNode[NodeData]] = {}
        sorted_paths = sorted(self.paths.keys(), key=lambda p: len(p.parts))

        for path in sorted_paths:
            node_data = self.paths[path]
            parent_path = path.parent
            if parent_path == self.root.data.path:
                parent_node = self.root
            elif parent_path in path_to_node:
                parent_node = path_to_node[parent_path]
            else:
                continue
            self.create_and_add_node(node_data=node_data, tree_node=parent_node)
            path_to_node[path] = parent_node.children[-1]

    def toggle_paths_without_status(
        self, *, tree_node: TreeNode[NodeData], show_unchanged: bool
    ) -> None:
        current_unchanged_files: list[TreeNode[NodeData]] = [
            child
            for child in tree_node.children
            if child.data is not None
            and child.data.path_kind == PathKind.FILE
            and child.data.status == StatusCode.file_no_status
        ]
        current_unchanged_dirs: list[TreeNode[NodeData]] = [
            child
            for child in tree_node.children
            if child.data is not None
            and child.data.path_kind == PathKind.DIR
            and child.data.status == StatusCode.dir_no_status
        ]
        all_unchanged = current_unchanged_files + current_unchanged_dirs
        for tree_node in all_unchanged:
            if tree_node.data is None:
                raise ValueError(f"tree_node data is None in {self.name}")
            if show_unchanged is True and tree_node not in all_unchanged:
                self.create_and_add_node(node_data=tree_node.data, tree_node=tree_node)
            elif show_unchanged is False and tree_node in all_unchanged:
                tree_node.remove()

    @on(Tree.NodeSelected)
    def send_node_context_message(self, event: Tree.NodeSelected[NodeData]) -> None:
        if event.node.data is None:
            raise ValueError("event.node.data is None in send_node_context")
        if self.ids.canvas_name == TabName.apply:
            self.post_message(CurrentApplyNodeMsg(event.node.data))
        elif self.ids.canvas_name == TabName.re_add:
            self.post_message(CurrentReAddNodeMsg(event.node.data))


class ExpandedTree(TreeBase):

    def __init__(self, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(self.ids, tree_name=TreeName.expanded_tree)

    def populate_dest_dir(self) -> None:
        self.create_all_nodes()
        for child in self.root.children:
            if child.data is not None and child.data.path_kind == PathKind.DIR:
                child.expand()
        self.update_expanded_nodes()
        self.update_visible_nodes()

    def expand_all_nodes(self, tree_node: TreeNode[NodeData]) -> None:
        for child in tree_node.children:
            if child.data is not None and child.data.path_kind == PathKind.DIR:
                child.expand()
                self.expand_all_nodes(child)

    def watch_unchanged(self) -> None:
        for tree_node in self.expanded_nodes:
            self.toggle_paths_without_status(
                tree_node=tree_node, show_unchanged=self.unchanged
            )

    @on(TreeBase.NodeExpanded)
    def add_node_children(self, event: TreeBase.NodeExpanded[NodeData]) -> None:
        event.stop()
        self.update_expanded_nodes()
        self.update_visible_nodes()

    @on(Tree.NodeCollapsed)
    def on_node_collapsed(self, event: Tree.NodeCollapsed[NodeData]) -> None:
        event.stop()
        self.update_expanded_nodes()
        self.update_visible_nodes()


class ListTree(TreeBase):

    def __init__(self, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(self.ids, tree_name=TreeName.list_tree)

    # will be implemented later after ManagedTree and ExpandedTree are done
    def populate_dest_dir(self) -> None:
        pass


class ManagedTree(TreeBase):

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(self.ids, tree_name=TreeName.managed_tree)

    def populate_dest_dir(self) -> None:
        self.create_all_nodes()
        self.update_expanded_nodes()
        self.update_visible_nodes()

    def watch_unchanged(self) -> None:
        for node in self.expanded_nodes:
            self.toggle_paths_without_status(
                tree_node=node, show_unchanged=self.unchanged
            )

    @on(TreeBase.NodeExpanded)
    def add_node_children(self, event: TreeBase.NodeExpanded[NodeData]) -> None:
        self.update_expanded_nodes()
        self.update_visible_nodes()

    @on(Tree.NodeCollapsed)
    def on_node_collapsed(self, event: Tree.NodeCollapsed[NodeData]) -> None:
        self.update_expanded_nodes()
        self.update_visible_nodes()
