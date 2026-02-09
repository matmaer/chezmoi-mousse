from pathlib import Path

from textual import on
from textual.reactive import reactive
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from chezmoi_mousse import AppIds, AppType, Chars, NodeData, TabName, Tcss, TreeName

from .messages import CurrentApplyNodeMsg, CurrentReAddNodeMsg

__all__ = ["ListTree", "ManagedTree"]


class TreeBase(Tree[NodeData], AppType):

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded

    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, ids: "AppIds", *, tree_name: TreeName) -> None:
        super().__init__(
            label="root", id=ids.tree_id(tree=tree_name), classes=Tcss.tree_widget
        )
        self.ids = ids
        assert self.app.paths is not None
        if self.ids.canvas_name == TabName.apply:
            self.dir_nodes = self.app.paths.apply_dir_node_dict
        else:
            self.dir_nodes = self.app.paths.re_add_dir_node_dict

    def on_mount(self) -> None:
        self.show_root = False
        self.border_title = " destDir "
        self.add_class(Tcss.border_title_top)

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
        assert self.app.paths is not None
        for dir_node in self.dir_nodes.values():
            for file_path in dir_node.status_files:
                # only add files as leaves, if they were not added already.
                if not any(
                    child.data and child.data.path == file_path
                    for child in self.root.children
                ):
                    # show relative path from dest_dir as label
                    relative_path = file_path.relative_to(self.app.cmd_results.dest_dir)
                    self.root.add_leaf(
                        str(relative_path), data=NodeData(path=file_path)
                    )


class ManagedTree(TreeBase):

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(ids, tree_name=TreeName.managed_tree)

    def populate_dest_dir(self) -> None:
        self.clear()
        nodes: dict[Path, TreeNode[NodeData]] = {
            self.app.cmd_results.dest_dir: self.root
        }
        self.root.data = NodeData(path=self.app.cmd_results.dest_dir)
        # Sort directories by path depth to ensure parents are added before children
        for dir_path in sorted(self.dir_nodes.keys(), key=lambda p: len(p.parts)):
            dir_node = self.dir_nodes[dir_path]
            if dir_path == self.app.cmd_results.dest_dir:
                # Add files directly under the root
                for file_path, _ in dir_node.status_files.items():
                    self.root.add_leaf(file_path.name, data=NodeData(path=file_path))
            else:
                parent_node: TreeNode[NodeData] = nodes[dir_path.parent]
                new_node = parent_node.add(dir_path.name, data=NodeData(path=dir_path))
                nodes[dir_path] = new_node
                # Add files as leaves under this directory
                for file_path, _ in dir_node.status_files.items():
                    new_node.add_leaf(file_path.name, data=NodeData(path=file_path))
