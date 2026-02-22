from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from chezmoi_mousse import AppType, Chars, StatusCode, TabName, Tcss, TreeName

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds, DirNode

from .messages import CurrentApplyNodeMsg, CurrentReAddNodeMsg

__all__ = ["ListTree", "ManagedTree"]


class TreeBase(Tree[Path], AppType):

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded

    def __init__(self, ids: "AppIds", *, tree_name: TreeName) -> None:
        super().__init__(
            label="root", id=ids.tree_id(tree=tree_name), classes=Tcss.tree_widget
        )
        self.ids = ids
        self.tree_name = tree_name

    def on_mount(self) -> None:
        self.show_root = False
        self.border_title = " destDir "
        self.add_class(Tcss.border_title_top)
        self.make_node_colors_dict()

    @property
    def dir_nodes(self) -> dict[Path, "DirNode"]:
        if self.ids.canvas_name == TabName.apply:
            return self.app.apply_dir_nodes
        else:
            return self.app.re_add_dir_nodes

    def get_all_nodes(self) -> list[TreeNode[Path]]:
        # BFS approach
        all_nodes: list[TreeNode[Path]] = []
        to_visit = [self.root]  # Start with root in the queue
        while to_visit:
            node = to_visit.pop(0)  # Dequeue the next node
            all_nodes.append(node)  # Add to results
            to_visit.extend(node.children)  # Enqueue children
        return all_nodes

    def make_node_colors_dict(self) -> None:
        self.node_colors: dict[str, str] = {
            StatusCode.Added: self.app.theme_variables["text-success"],
            StatusCode.Deleted: self.app.theme_variables["text-error"],
            StatusCode.Modified: self.app.theme_variables["text-warning"],
            StatusCode.No_Change: self.app.theme_variables["warning-darken-2"],
            StatusCode.Run: self.app.theme_variables["error"],
            StatusCode.No_Status: self.app.theme_variables["text-secondary"],
        }

    def create_colored_label(self, path: Path) -> str:
        label_text = (
            str(path.relative_to(self.app.dest_dir))
            if self.tree_name == TreeName.list_tree
            else path.name
        )

        # Get status code for the path
        status = StatusCode.No_Status
        for dir_node in self.dir_nodes.values():
            if path in dir_node.status_files_in:
                status = dir_node.status_files_in[path]
                break
        else:
            status = self.dir_nodes[path].dir_status

        # Get color and create styled label
        color = self.node_colors.get(status, self.node_colors[StatusCode.No_Status])
        italic = " italic" if not path.exists() else ""
        return f"[{color}{italic}]{label_text}[/]"

    def populate_node(self, tree_node: TreeNode[Path], dir_path: Path) -> None:
        dir_node = self.dir_nodes[dir_path]
        for sub_dir, _ in dir_node.tree_status_dirs_in.items():
            child_node = tree_node.add(self.create_colored_label(sub_dir), data=sub_dir)
            self.populate_node(child_node, sub_dir)
        for file_path, _ in dir_node.status_files_in.items():
            tree_node.add_leaf(self.create_colored_label(file_path), data=file_path)

    @on(Tree.NodeSelected)
    def send_node_context_message(self, event: Tree.NodeSelected[Path]) -> None:
        if event.node.data is None:
            raise ValueError("event.node.data is None in send_node_context")
        if self.ids.canvas_name == TabName.apply:
            self.post_message(CurrentApplyNodeMsg(event.node.data))
        elif self.ids.canvas_name == TabName.re_add:
            self.post_message(CurrentReAddNodeMsg(event.node.data))


class ListTree(TreeBase):

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(ids, tree_name=TreeName.list_tree)

    def populate_tree(self) -> None:
        self.clear()
        for dir_node in self.dir_nodes.values():
            for file_path in dir_node.status_files_in:
                # only add files as leaves, if they were not added already.
                if not any(
                    child.data and child.data == file_path
                    for child in self.root.children
                ):
                    colored_label = self.create_colored_label(file_path)
                    self.root.add_leaf(colored_label, data=file_path)

    def get_all_nodes(self) -> list[TreeNode[Path]]:
        return [child for child in self.root.children if child.data is not None]


class ManagedTree(TreeBase):

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(ids, tree_name=TreeName.managed_tree)

    def populate_tree(self) -> None:
        current_nodes = self.get_all_nodes()
        expanded_paths = {
            node.data
            for node in current_nodes
            if node.is_expanded and node.data is not None
        }
        self.clear()
        self.root.data = self.app.dest_dir
        self.populate_node(self.root, self.app.dest_dir)
        for node in self.get_all_nodes():
            if node.data in expanded_paths:
                node.expand()

    def get_all_nodes(self) -> list[TreeNode[Path]]:
        # BFS approach
        all_nodes: list[TreeNode[Path]] = []
        to_visit = [self.root]  # Start with root in the queue
        while to_visit:
            node = to_visit.pop(0)  # Dequeue the next node
            all_nodes.append(node)  # Add to results
            to_visit.extend(node.children)  # Enqueue children
        return all_nodes
