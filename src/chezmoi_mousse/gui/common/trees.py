"""Contains subclassed textual classes shared between the ApplyTab and ReAddTab."""

from pathlib import Path

from textual import on
from textual.reactive import reactive
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from chezmoi_mousse import (
    AppIds,
    AppType,
    Chars,
    NodeData,
    PathKind,
    PathNode,
    StatusCode,
    TabName,
    Tcss,
    TreeName,
)

from .messages import CurrentApplyNodeMsg, CurrentReAddNodeMsg

type NodeDict = dict[Path, NodeData]

__all__ = ["ExpandedTree", "ListTree", "ManagedTree", "TreeBase"]


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
        self.expanded_nodes: list[TreeNode[NodeData]] = []
        self.visible_nodes: list[TreeNode[NodeData]] = []

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

    def create_and_add_node(self, tree_node: TreeNode[NodeData]) -> None:
        if tree_node.data is None:
            raise ValueError("tree_node is None")
        italic = " italic" if not tree_node.data.found else ""
        color = self.node_colors[tree_node.data.status]
        node_label = f"[{color}" f"{italic}]{tree_node.data.path.name}[/]"
        if tree_node.data.path_kind == PathKind.FILE:
            tree_node.add_leaf(label=node_label, data=tree_node.data)
        else:
            tree_node.add(label=node_label, data=tree_node.data)

    def create_all_nodes(self) -> None:
        if self.app.dest_dir is None:
            raise ValueError("self.app.dest_dir is None")

        # Track created TreeNodes to find parents when building tree
        node_map: dict[Path, TreeNode[NodeData]] = {self.app.dest_dir: self.root}

        def create_node_data(path_node: "PathNode") -> NodeData:
            return NodeData(
                found=path_node.found,
                path_kind=path_node.path_kind,
                path=path_node.path,
                status=(
                    path_node.status_pair[1]
                    if self.ids.canvas_name == TabName.apply
                    else path_node.status_pair[0]
                ),
            )

        def ensure_parent_exists(path: Path) -> TreeNode[NodeData]:
            if path in node_map:
                return node_map[path]

            # Create the parent's parent first (recursion)
            parent_node = ensure_parent_exists(path.parent)

            # Create this intermediate directory node
            color = self.node_colors[StatusCode.dir_no_status]
            intermediate_node = parent_node.add(
                label=f"[{color}]{path.name}[/]", data=None
            )
            node_map[path] = intermediate_node
            return intermediate_node

        # Combine sorted dirs and files
        sorted_dirs = sorted(self.app.managed.dirs.values(), key=lambda n: n.path)
        sorted_files = sorted(self.app.managed.files.values(), key=lambda n: n.path)

        for path_node in sorted_dirs + sorted_files:
            node_data = create_node_data(path_node)
            path = node_data.path

            # Ensure parent exists
            parent_node = ensure_parent_exists(path.parent)

            # Create the actual node
            italic = " italic" if not node_data.found else ""
            color = self.node_colors[node_data.status]
            node_label = f"[{color}{italic}]{path.name}[/]"

            if node_data.path_kind == PathKind.FILE:
                new_node = parent_node.add_leaf(label=node_label, data=node_data)
            else:
                new_node = parent_node.add(label=node_label, data=node_data)

            node_map[path] = new_node

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
                self.create_and_add_node(tree_node)
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
