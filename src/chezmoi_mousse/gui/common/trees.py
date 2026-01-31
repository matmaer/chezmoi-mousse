from pathlib import Path

from textual import on
from textual.reactive import reactive
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from chezmoi_mousse import AppIds, AppType, Chars, NodeData, TabName, Tcss, TreeName

from .messages import CurrentApplyNodeMsg, CurrentReAddNodeMsg


class TreeBase(Tree[NodeData], AppType):

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded

    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, ids: "AppIds", *, tree_name: TreeName) -> None:
        super().__init__(
            label="root", id=ids.tree_id(tree=tree_name), classes=Tcss.tree_widget
        )
        self.ids = ids
        if self.ids.canvas_name == TabName.apply:
            self.dir_nodes = self.app.apply_dir_nodes
        else:
            self.dir_nodes = self.app.re_add_dir_nodes

    def on_mount(self) -> None:
        self.show_root = False

    def add_path_to_tree(
        self,
        path: Path,
        root: TreeNode[NodeData],
        nodes: dict[Path, TreeNode[NodeData]],
    ) -> TreeNode[NodeData]:
        if path in nodes:
            return nodes[path]
        parent = path.parent
        if parent != path:  # not root
            parent_node = self.add_path_to_tree(parent, root, nodes)
        else:
            parent_node = root
        node = parent_node.add(path.name, data=NodeData(found=True, path=path))
        nodes[path] = node
        return node

    @on(Tree.NodeSelected)
    def send_node_context_message(self, event: Tree.NodeSelected[NodeData]) -> None:
        if event.node.data is None:
            raise ValueError("event.node.data is None in send_node_context")
        if self.ids.canvas_name == TabName.apply:
            self.post_message(CurrentApplyNodeMsg(event.node.data))
        elif self.ids.canvas_name == TabName.re_add:
            self.post_message(CurrentReAddNodeMsg(event.node.data))


class ListTree(TreeBase):

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(ids, tree_name=TreeName.list_tree)

    def populate_dest_dir(self) -> None:
        self.clear()
        for dir_node in self.dir_nodes.values():
            for file_path in dir_node.status_files | dir_node.x_files:
                self.root.add(str(file_path), data=NodeData(found=True, path=file_path))


class ManagedTree(TreeBase):

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(ids, tree_name=TreeName.managed_tree)

    def populate_dest_dir(self) -> None:
        self.clear()
        nodes: dict[Path, TreeNode[NodeData]] = {}
        assert self.app.dest_dir is not None
        nodes[self.app.dest_dir] = self.root
        for dir_path in self.dir_nodes:
            self.add_path_to_tree(dir_path, self.root, nodes)
        for dir_node in self.dir_nodes.values():
            for file_path in dir_node.status_files | dir_node.x_files:
                self.add_path_to_tree(file_path, self.root, nodes)
