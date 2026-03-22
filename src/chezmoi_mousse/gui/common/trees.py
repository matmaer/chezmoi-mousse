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
        self.expanded_nodes: list[TreeNode[Path]] = []
        self.collapsed_nodes: list[TreeNode[Path]] = []
        # Track nodes added for "unchanged" (x) items so we can remove them safely
        self._x_nodes: list[TreeNode[Path]] = []

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
        # Reset tracked expanded/collapsed lists when rebuilding the tree
        self.expanded_nodes = []
        self.collapsed_nodes = []
        # Reset tracked x-nodes when rebuilding the tree
        self._x_nodes = []
        self.clear()
        self.root.data = CMD.cache.dest_dir
        color = self.app.theme_variables["text-primary"]
        self.root.label = f"[{color} bold]{CMD.cache.dest_dir}[/]"
        self.root.expand()
        self.expanded_nodes.append(self.root)
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
            if self.expand_all:
                child_node.expand()

        for file_path in CMD.cache.sets.status_files_in(
            tree_node.data, recursive=False
        ):
            tree_node.add_leaf(self.create_colored_label(file_path), data=file_path)
        if self.unchanged:
            self._populate_x_dir(tree_node, tree_node.data)

    def _populate_x_dir(self, tree_node: TreeNode[Path], dir_path: Path) -> None:
        if tree_node.data is None:
            return

        # Add files, avoiding duplicates
        for x_file in sorted(CMD.cache.sets.x_files_in(dir_path)):
            if not any((child.data == x_file) for child in tree_node.children):
                new_leaf = tree_node.add_leaf(f"[dim]{x_file.name}[/]", x_file)
                # track so we only remove these later
                self._x_nodes.append(new_leaf)

        # Add sub-directories, avoiding duplicates
        for x_sub_dir in sorted(CMD.cache.sets.x_dirs_in(tree_node.data)):
            if any((child.data == x_sub_dir) for child in tree_node.children):
                # find existing node and recurse into it
                existing = next(
                    (c for c in tree_node.children if c.data == x_sub_dir), None
                )
                if existing is not None:
                    if self.expand_all:
                        existing.expand()
                    self._populate_x_dir(existing, x_sub_dir)
                continue

            new_x_node = tree_node.add(f"[dim]{x_sub_dir.name}[/]", data=x_sub_dir)
            # track so we only remove these later
            self._x_nodes.append(new_x_node)
            if self.expand_all:
                new_x_node.expand()
            self._populate_x_dir(new_x_node, x_sub_dir)

    def get_all_nodes(self) -> list[TreeNode[Path]]:
        # BFS approach
        all_nodes: list[TreeNode[Path]] = []
        to_visit = [self.root]  # Start with root in the queue
        while to_visit:
            node = to_visit.pop(0)  # Dequeue the next node
            all_nodes.append(node)  # Add to results
            to_visit.extend(node.children)  # Enqueue children
        return all_nodes

    @property
    def dir_nodes(self) -> list[TreeNode[Path]]:
        return [node for node in self.get_all_nodes() if node.allow_expand is True]

    @property
    def file_nodes(self) -> list[TreeNode[Path]]:
        return [node for node in self.get_all_nodes() if node.allow_expand is False]

    @on(Tree.NodeCollapsed)
    def update_collapsed_nodes(self, event: Tree.NodeCollapsed[Path]) -> None:
        if event.node in self.expanded_nodes:
            self.expanded_nodes.remove(event.node)
        if event.node not in self.collapsed_nodes:
            self.collapsed_nodes.append(event.node)

    @on(Tree.NodeExpanded)
    def update_expanded_nodes(self, event: Tree.NodeExpanded[Path]) -> None:
        if event.node in self.collapsed_nodes:
            self.collapsed_nodes.remove(event.node)
        if event.node not in self.expanded_nodes:
            self.expanded_nodes.append(event.node)

    def watch_expand_all(self, expand_all: bool) -> None:
        if expand_all:
            for node in self.dir_nodes:
                with contextlib.suppress(Exception):
                    node.expand()
        else:
            for node in self.dir_nodes:
                with contextlib.suppress(Exception):
                    node.collapse()

    def watch_unchanged(self, unchanged: bool) -> None:
        if unchanged is True:
            for node in self.get_all_nodes():
                if node.data is not None and node.data in (
                    CMD.cache.sets.n_dirs | CMD.cache.sets.status_dirs
                ):
                    self._populate_x_dir(node, node.data)
        elif unchanged is False:
            # Remove any previously added "x" nodes (files or dirs) that we tracked
            for node in list(self._x_nodes):
                with contextlib.suppress(Exception):
                    node.remove()
            self._x_nodes = []
