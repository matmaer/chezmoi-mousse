import contextlib
from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.reactive import reactive
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from chezmoi_mousse import CMD, AppType, Chars, StatusCode, TabLabel, Tcss, TreeName

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

from .messages import CurrentApplyNodeMsg, CurrentReAddNodeMsg

__all__ = ["ListTree", "ManagedTree"]


class TreeBase(Tree[Path], AppType):

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded

    def __init__(self, ids: "AppIds", *, tree_name: TreeName) -> None:
        super().__init__(
            label=f" {CMD.cache.dest_dir} ",
            id=ids.tree_id(tree=tree_name),
            classes=Tcss.tree_widget,
        )
        self.ids = ids
        self.tree_name = tree_name

    def create_colored_label(self, path: Path) -> str:
        label_text = (
            str(path.relative_to(CMD.cache.dest_dir))
            if self.tree_name == TreeName.list_tree
            else path.name
        )

        # Get status code for the path
        status = CMD.cache.get_path_status(path, self.ids.canvas_name)
        color_var = status.color_var
        if status == StatusCode.Space and path in CMD.cache.sets.n_dirs:
            color_var = "text-secondary"

        # Get color and create styled label
        color = self.app.theme_var_to_hex(color_var)
        italic = " italic" if not path.exists() else ""
        return f"[{color}{italic}]{label_text}[/]"

    @on(Tree.NodeSelected)
    def send_node_context_message(self, event: Tree.NodeSelected[Path]) -> None:
        if event.node.data is None:
            raise ValueError("event.node.data is None in send_node_context")
        if self.ids.canvas_name == TabLabel.apply:
            self.post_message(CurrentApplyNodeMsg(event.node.data))
        elif self.ids.canvas_name == TabLabel.re_add:
            self.post_message(CurrentReAddNodeMsg(event.node.data))


class ListTree(TreeBase):

    unchanged: reactive[bool] = reactive(False)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(ids, tree_name=TreeName.list_tree)

    def on_mount(self) -> None:
        self.show_root = False

    def populate_tree(self) -> None:
        self.clear()
        self.root.data = CMD.cache.dest_dir
        self.root.expand()
        all_status_files = CMD.cache.get_status_files_in(
            CMD.cache.dest_dir, self.ids.canvas_name, recursive=True
        )
        for file_path in sorted(all_status_files.keys()):
            self.root.add_leaf(self.create_colored_label(file_path), data=file_path)
        self.select_node(self.root)

    def get_all_nodes(self) -> list[TreeNode[Path]]:
        return [child for child in self.root.children if child.data is not None]

    def watch_unchanged(self, unchanged: bool) -> None:
        if unchanged is True:
            for x_file in sorted(CMD.cache.sets.x_files):
                rel_path = str(x_file.relative_to(CMD.cache.dest_dir))
                self.root.add_leaf(f"[dim]{rel_path}[/]", x_file)
        elif unchanged is False:
            for node in self.get_all_nodes():
                if node.data in CMD.cache.sets.x_files:
                    with contextlib.suppress(Exception):
                        node.remove()


class ManagedTree(TreeBase):

    unchanged: reactive[bool] = reactive(False)
    expand_all: reactive[bool] = reactive(False)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(ids, tree_name=TreeName.managed_tree)
        self.old_expanded_nodes: list[TreeNode[Path]] = []

    def on_mount(self) -> None:
        self.guide_depth: int = 3
        self.root.expand()

    def populate_tree(self) -> None:
        current_nodes = self.get_all_nodes()
        expanded_paths = {
            node.data
            for node in current_nodes
            if node.is_expanded and node.data is not None
        }
        self.clear()
        self.root.data = CMD.cache.dest_dir
        color = self.app.theme_variables["text-primary"]
        self.root.label = f"[{color} bold]{CMD.cache.dest_dir}[/]"
        self.root.expand()
        self.root.allow_expand = False
        self._populate_node(self.root)
        for node in self.get_all_nodes():
            if node.data in expanded_paths:
                node.expand()
        self.select_node(self.root)

    def _populate_node(self, tree_node: TreeNode[Path]) -> None:
        if tree_node.data is None:
            raise ValueError("tree_node.data is None in _populate_node")

        n_dirs_in: set[Path] = CMD.cache.sets.n_dirs_in(tree_node.data)
        status_dirs_in: set[Path] = CMD.cache.sets.status_dirs_in(tree_node.data)
        dirs_to_add = sorted(n_dirs_in | status_dirs_in, key=lambda p: p.name)
        for dir in dirs_to_add:
            child_node = tree_node.add(self.create_colored_label(dir), data=dir)
            self._populate_node(child_node)
        for file_path in CMD.cache.sets.status_files_in(
            tree_node.data, recursive=False
        ):
            tree_node.add_leaf(self.create_colored_label(file_path), data=file_path)

    def _populate_x_node(self, tree_node: TreeNode[Path], dir_path: Path) -> None:
        if tree_node.data is None:
            return
        for x_file in sorted(CMD.cache.sets.x_files_in(dir_path)):
            tree_node.add_leaf(f"[dim]{x_file.name}[/]", x_file)

        for x_sub_dir in sorted(CMD.cache.sets.x_dirs_in(tree_node.data)):
            new_x_node = tree_node.add(f"[dim]{x_sub_dir.name}[/]", data=x_sub_dir)
            if self.expand_all:
                new_x_node.expand()
            self._populate_x_node(new_x_node, x_sub_dir)

    def get_all_nodes(self) -> list[TreeNode[Path]]:
        # BFS approach
        all_nodes: list[TreeNode[Path]] = []
        to_visit = [self.root]  # Start with root in the queue
        while to_visit:
            node = to_visit.pop(0)  # Dequeue the next node
            all_nodes.append(node)  # Add to results
            to_visit.extend(node.children)  # Enqueue children
        return all_nodes

    def watch_expand_all(self, expand_all: bool) -> None:
        nodes_before_toggle = self.get_all_nodes()
        if expand_all is True:
            self.old_expanded_nodes = [
                node for node in nodes_before_toggle if node.is_expanded
            ]
            for node in nodes_before_toggle:
                node.expand()
        else:
            for node in nodes_before_toggle:
                if node not in self.old_expanded_nodes:
                    node.collapse()

    def watch_unchanged(self, unchanged: bool) -> None:
        nodes_before_toggle = self.get_all_nodes()
        if unchanged is True:
            for node in nodes_before_toggle:
                if node.data is None:
                    raise ValueError("node.data is None")

                if CMD.cache.sets.has_status_paths(node.data):
                    self._populate_x_node(node, node.data)
                    if self.expand_all:
                        node.expand()

        elif unchanged is False:
            for tree_node in nodes_before_toggle:
                if tree_node.data in CMD.cache.sets.x_files or (
                    tree_node.data in CMD.cache.sets.x_dirs
                    and tree_node.data not in CMD.cache.sets.n_dirs
                ):
                    with contextlib.suppress(Exception):
                        tree_node.remove()
