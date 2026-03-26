from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Label, Tree
from textual.widgets.tree import TreeNode

from chezmoi_mousse import CMD, AppType, Chars, StatusCode, TabLabel, Tcss

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

from .actionables import OpBtnEnum, OpButton
from .messages import CurrentApplyNodeMsg, CurrentReAddNodeMsg

__all__ = ["ManagedTree", "TreeSwitcher"]


class CurrentNodes(NamedTuple):
    dirs: set[TreeNode[Path]]
    files: set[TreeNode[Path]]

    @property
    def all_nodes(self) -> set[TreeNode[Path]]:
        return self.dirs | self.files

    @property
    def x_files(self) -> set[TreeNode[Path]]:
        return {node for node in self.files if node.data in CMD.cache.sets.x_files}


class TreeSwitcher(Vertical, AppType):

    unchanged: reactive[bool] = reactive(False)
    expand_all: reactive[bool] = reactive(False)

    def __init__(self, ids: "AppIds"):
        super().__init__(id=ids.container.left_side, classes=Tcss.tab_left_vertical)
        self.ids = ids
        self.old_expanded_nodes: list[TreeNode[Path]] = []

    def compose(self) -> ComposeResult:
        yield Label("destDir tree", classes=Tcss.dest_dir_tree_label)
        yield ManagedTree(self.ids)
        yield OpButton(
            btn_enum=OpBtnEnum.refresh_tree,
            btn_id=self.ids.op_btn.refresh_tree,
            app_ids=self.ids,
        )

    def on_mount(self) -> None:
        managed_tree = self.query_one(self.ids.managed_tree_q, ManagedTree)
        managed_tree.add_class(Tcss.tree_widgets)
        refresh_btn = self.query_one(self.ids.op_btn.refresh_tree_q, OpButton)
        refresh_btn.remove_class(Tcss.operate_button)
        refresh_btn.add_class(Tcss.refresh_button)


class ManagedTree(Tree[Path], AppType):

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded

    unchanged: reactive[bool] = reactive(False)
    expand_all: reactive[bool] = reactive(False)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(label="", id=ids.managed_tree, classes=Tcss.tree_widget)
        self.ids = ids
        self.current_nodes = CurrentNodes(dirs=set(), files=set())
        self._previous_expanded: set[Path] = set()
        self._x_nodes: set[TreeNode[Path]] = set()

    def on_mount(self) -> None:
        self._first_time_populating = True
        self.guide_depth: int = 3
        self.root.expand()

    def _create_colored_label(self, path: Path) -> str:
        status = CMD.cache.get_path_status(path, self.ids)
        color_var = status.color_var
        if status == StatusCode.Space and path in CMD.cache.sets.n_dirs:
            color_var = "text-secondary"
        color = self.app.theme_var_to_hex(color_var)
        italic = " italic" if not path.exists() else ""
        return f"[{color}{italic}]{path.name}[/]"

    @on(Tree.NodeSelected)
    def send_node_context_message(self, event: Tree.NodeSelected[Path]) -> None:
        if event.node.data is None:
            raise ValueError("event.node.data is None in send_node_context")
        if self.ids.canvas_name == TabLabel.apply:
            self.post_message(CurrentApplyNodeMsg(event.node.data))
        elif self.ids.canvas_name == TabLabel.re_add:
            self.post_message(CurrentReAddNodeMsg(event.node.data))

    def populate_tree(self) -> None:
        self.clear()
        self.current_nodes.dirs.clear()
        self.current_nodes.files.clear()
        self.root.data = CMD.cache.dest_dir
        color = self.app.theme_variables["text-primary"]
        self.root.label = f"[{color} bold]{CMD.cache.dest_dir.name}[/]"
        self.root.expand()
        self.root.allow_expand = False  # to prevent the root node from being collapsed
        self._populate_root_node_recursive(self.root)
        if self._first_time_populating:
            for node in self.current_nodes.dirs:
                if node.data != CMD.cache.dest_dir:
                    node.collapse()
            self._first_time_populating = False
        self.select_node(self.root)

    def _update_current_nodes(self) -> CurrentNodes:
        # BFS approach
        all_dir_nodes: set[TreeNode[Path]] = {self.root}
        all_file_nodes: set[TreeNode[Path]] = set()
        to_visit = [self.root]  # Start with root in the queue
        while to_visit:
            node = to_visit.pop(0)  # Dequeue the next node
            if node.data in CMD.cache.sets.managed_dirs:
                all_dir_nodes.add(node)  # Add to results
            elif node.data in CMD.cache.sets.managed_files:
                all_file_nodes.add(node)
            to_visit.extend(node.children)  # Enqueue children
        current = CurrentNodes(dirs=all_dir_nodes, files=all_file_nodes)
        # keep `self.current_nodes` in sync for callers that rely on it
        self.current_nodes = current
        return current

    def select_node_by_path(self, path: Path) -> None:
        for parent in reversed(path.parents):
            for node in self.current_nodes.dirs:
                if node.data == parent and node.is_expanded is False:
                    node.expand()
                    break
        self._update_current_nodes()
        for node in self.current_nodes.all_nodes:
            if node.data == path:
                self.select_node(node)
                break

    def _insert_dir(
        self, parent_node: TreeNode[Path], dir_path: Path
    ) -> TreeNode[Path]:
        child_dir_nodes: list[TreeNode[Path]] = [
            n for n in parent_node.children if n.data in CMD.cache.sets.managed_dirs
        ]
        if dir_path not in CMD.cache.sets.n_dirs:
            node_label = f"[dim]{dir_path.name}[/]"
        else:
            node_label = self._create_colored_label(dir_path)
        before_node = next(
            (node for node in child_dir_nodes if node_label > str(node.data)), None
        )
        return parent_node.add(node_label, data=dir_path, before=before_node)

    def _insert_file(self, parent_node: TreeNode[Path], file_path: Path) -> None:
        child_file_nodes: list[TreeNode[Path]] = [
            n for n in parent_node.children if n.data in CMD.cache.sets.managed_files
        ]
        if file_path in CMD.cache.sets.x_files:
            node_label = f"[dim]{file_path.name}[/]"
        else:
            node_label = self._create_colored_label(file_path)
        before_node = next(
            (node for node in child_file_nodes if node_label > str(node.data)), None
        )
        parent_node.add_leaf(node_label, data=file_path, before=before_node)

    def _populate_root_node_recursive(self, tree_node: TreeNode[Path]) -> None:
        if tree_node.data is None:
            raise ValueError("tree_node.data is None in _populate_node")
        n_dirs_in: set[Path] = CMD.cache.sets.n_dirs_in(tree_node.data)
        status_dirs_in: set[Path] = CMD.cache.sets.status_dirs_in(tree_node.data)
        for dir in n_dirs_in | status_dirs_in:
            child_node = self._insert_dir(tree_node, dir)
            for file_path in CMD.cache.sets.status_files_in(dir):
                self._insert_file(child_node, file_path)
            self._populate_root_node_recursive(child_node)
        self._update_current_nodes()

    def _add_x_paths_to_root_recursive(self, tree_node: TreeNode[Path]) -> None:
        if tree_node.data is None:
            raise ValueError("tree_node.data is None")
        x_dirs_in = CMD.cache.sets.x_dirs_in(tree_node.data)
        for file_path in CMD.cache.sets.x_files_in(tree_node.data):
            self._insert_file(tree_node, file_path)
        for dir_path in {p for p in x_dirs_in if p not in CMD.cache.sets.n_dirs}:
            child = self._insert_dir(tree_node, dir_path)
            x_files_in = CMD.cache.sets.x_files_in(dir_path)
            if not x_files_in:
                continue
            child.expand()
            for file_path in x_files_in:
                self._insert_file(child, file_path)
            self._add_x_paths_to_root_recursive(child)
        self._update_current_nodes()

    def _remove_all_x_paths(self):
        for file_node in self.current_nodes.files:
            if file_node.data in CMD.cache.sets.x_files:
                file_node.remove()
        for dir_node in self.current_nodes.dirs:
            if (
                dir_node.data in CMD.cache.sets.x_dirs
                and dir_node.data not in CMD.cache.sets.n_dirs
            ):
                dir_node.remove()
        self._update_current_nodes()

    @on(Tree.NodeCollapsed)
    def update_collapsed_nodes(self, event: Tree.NodeCollapsed[Path]) -> None:
        if self.expand_all:
            return
        if event.node in self.current_nodes.dirs and event.node.data is not None:
            self._previous_expanded.discard(event.node.data)

    @on(Tree.NodeExpanded)
    def update_expanded_nodes(self, event: Tree.NodeExpanded[Path]) -> None:
        if self.expand_all:
            return
        if event.node.data is not None:
            self._previous_expanded.add(event.node.data)

    def watch_expand_all(self, expand_all: bool) -> None:
        if expand_all is True:
            self._previous_expanded = {
                node.data
                for node in self.current_nodes.dirs
                if node.is_expanded and node.data is not None
            }
            for node in self.current_nodes.dirs:
                node.expand()
        elif expand_all is False:
            for node in self.current_nodes.dirs:
                if node.data not in self._previous_expanded:
                    node.collapse()

    def watch_unchanged(self, unchanged: bool) -> None:
        if unchanged is True:
            self._add_x_paths_to_root_recursive(self.root)
        elif unchanged is False:
            self._remove_all_x_paths()
        self._update_current_nodes()
