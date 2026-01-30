from pathlib import Path

from textual.reactive import reactive
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from chezmoi_mousse import AppIds, AppType, Chars, NodeData, Tcss, TreeName


class TreeBase(Tree[NodeData], AppType):

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded

    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, ids: "AppIds", *, tree_name: TreeName) -> None:
        super().__init__(
            label="root", id=ids.tree_id(tree=tree_name), classes=Tcss.tree_widget
        )
        self.ids = ids

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


class ListTree(TreeBase):

    def __init__(self, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(self.ids, tree_name=TreeName.list_tree)

    def populate_dest_dir(self) -> None:
        self.clear()
        root = self.root
        for dir_node in self.app.dir_nodes.values():
            for file_path in dir_node.status_files | dir_node.x_files:
                root.add(str(file_path), data=NodeData(found=True, path=file_path))


class ManagedTree(TreeBase):

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(self.ids, tree_name=TreeName.managed_tree)

    def populate_dest_dir(self) -> None:
        self.clear()
        nodes: dict[Path, TreeNode[NodeData]] = {}
        root = self.root
        assert self.app.dest_dir is not None
        nodes[self.app.dest_dir] = root
        for dir_path in self.app.dir_nodes:
            self.add_path_to_tree(dir_path, root, nodes)
        for dir_node in self.app.dir_nodes.values():
            for file_path in dir_node.status_files | dir_node.x_files:
                self.add_path_to_tree(file_path, root, nodes)
