from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Label, Tree
from textual.widgets.tree import TreeNode

from chezmoi_mousse import CMD, AppType, Chars, TabLabel, Tcss

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

from .actionables import OpBtnEnum, OpButton
from .messages import CurrentApplyNodeMsg, CurrentReAddNodeMsg

__all__ = ["ManagedTree", "TreeSwitcher"]


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

    unchanged: reactive[bool] = reactive(False, init=False)
    expand_all: reactive[bool] = reactive(False, init=False)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(label="", id=ids.managed_tree, classes=Tcss.tree_widget)
        self.ids = ids
        self._current_nodes = self._get_current_nodes()
        self._first_time_populating = True

    def on_mount(self) -> None:
        self.guide_depth: int = 3
        self.root.expand()

    @property
    def current_expanded(self) -> set[TreeNode[Path]]:
        return {n for n in self._current_nodes if n.is_expanded}

    @property
    def current_x_file_nodes(self) -> set[TreeNode[Path]]:
        return {n for n in self._current_nodes if n.data in CMD.cache.sets.x_files}

    @property
    def current_collapsed(self) -> set[TreeNode[Path]]:
        return {n for n in self._current_nodes if not n.is_expanded}

    def _update_expanded_nodes(self) -> None:
        if self.expand_all:
            self._populate_root_node_recursive(self.root)
        else:
            for node in self._get_current_nodes():
                node.collapse()

    def _create_colored_label(self, path: Path) -> str:
        status = CMD.cache.get_path_status(path, self.ids)
        color = "dim"
        color_var = status.color_var
        if path in CMD.cache.sets.n_dirs:
            color_var = "text-secondary"
            color = self.app.get_theme_var(color_var)
        elif path in CMD.cache.sets.status_dirs | CMD.cache.sets.status_files:
            color = self.app.get_theme_var(color_var)
        italic = " italic" if not path.exists() else ""
        return f"[{color}{italic}]{path.name}[/]"

    def populate_tree(self) -> None:
        self.clear()
        self.root.data = CMD.cache.dest_dir
        color = self.app.theme_variables["text-primary"]
        self.root.label = f"[{color} bold]{CMD.cache.dest_dir.name}[/]"
        self.root.expand()
        self.root.allow_expand = False  # to prevent the root node from being collapsed
        self._populate_root_node_recursive(self.root)
        if self._first_time_populating:
            # expand all switch is false by default
            current_nodes = self._get_current_nodes()
            for node in current_nodes:
                if (
                    node.data != CMD.cache.dest_dir
                    and node.data in CMD.cache.sets.managed_dirs
                ):
                    node.collapse()
            self._first_time_populating = False
        self.select_node(self.root)

    def _get_current_nodes(self) -> set[TreeNode[Path]]:
        # BFS approach
        all_dir_nodes: set[TreeNode[Path]] = set()
        all_file_nodes: set[TreeNode[Path]] = set()
        to_visit = [self.root]  # Start with root in the queue
        while to_visit:
            node = to_visit.pop(0)  # Dequeue the next node
            if node.data in CMD.cache.sets.managed_dirs:
                all_dir_nodes.add(node)  # Add to results
            elif node.data in CMD.cache.sets.managed_files:
                all_file_nodes.add(node)
            to_visit.extend(node.children)  # Enqueue children
        return all_dir_nodes | all_file_nodes

    def select_node_by_path(self, path: Path) -> None:
        current_nodes = self._get_current_nodes()
        current_dir_nodes = {
            n for n in current_nodes if n.data in CMD.cache.sets.managed_dirs
        }
        for parent in reversed(path.parents):
            for node in current_dir_nodes:
                if node.data == parent and node.is_expanded is False:
                    node.expand()
                    break
        for node in current_nodes:
            if node.data == path:
                self.select_node(node)
                break

    def _insert_dir(
        self, parent: TreeNode[Path], dir_path: Path
    ) -> TreeNode[Path] | None:
        child_dir_nodes: list[TreeNode[Path]] = [
            n for n in parent.children if n.data in CMD.cache.sets.managed_dirs
        ]
        if dir_path in {n.data for n in child_dir_nodes}:
            return None
        node_label = self._create_colored_label(dir_path)
        before_node = next(
            (node for node in child_dir_nodes if node_label > str(node.data)), None
        )
        return parent.add(node_label, data=dir_path, before=before_node)

    def _insert_file(self, parent: TreeNode[Path], file_path: Path) -> None:
        child_file_nodes = {
            n for n in parent.children if n.data in CMD.cache.sets.managed_files
        }
        if file_path in {n.data for n in child_file_nodes}:
            return
        node_label = self._create_colored_label(file_path)
        before_node = next(
            (node for node in child_file_nodes if node_label > str(node.data)), None
        )
        parent.add_leaf(node_label, data=file_path, before=before_node)

    def _populate_root_node_recursive(self, tree_node: TreeNode[Path]) -> None:
        if tree_node.data is None:
            raise ValueError("tree_node.data is None in _populate_node")
        n_dirs_in: set[Path] = CMD.cache.sets.n_dirs_in(tree_node.data)
        status_dirs_in: set[Path] = CMD.cache.sets.status_dirs_in(tree_node.data)
        for file_path in CMD.cache.sets.status_files_in(tree_node.data):
            self._insert_file(tree_node, file_path)
        for dir in n_dirs_in | status_dirs_in:
            child_node = self._insert_dir(tree_node, dir)
            if child_node is None:
                continue
            for file_path in CMD.cache.sets.status_files_in(dir):
                self._insert_file(child_node, file_path)
            self._populate_root_node_recursive(child_node)

    #################################
    # Watchers and message handling #
    #################################

    @on(Tree.NodeCollapsed)
    def update_collapsed_nodes(self, event: Tree.NodeCollapsed[Path]) -> None:
        event.stop()
        self._current_nodes = self._get_current_nodes()

    @on(Tree.NodeExpanded)
    def update_file_nodes(self, event: Tree.NodeExpanded[Path]) -> None:
        if self.unchanged:
            self._populate_root_node_recursive(event.node)
        if self.expand_all:
            self._populate_root_node_recursive(event.node)

    @on(Tree.NodeSelected)
    def send_node_context_message(self, event: Tree.NodeSelected[Path]) -> None:
        if event.node.data is None:
            raise ValueError("event.node.data is None in send_node_context")
        if self.ids.canvas_name == TabLabel.apply:
            self.post_message(CurrentApplyNodeMsg(event.node.data))
        elif self.ids.canvas_name == TabLabel.re_add:
            self.post_message(CurrentReAddNodeMsg(event.node.data))

    def watch_expand_all(self, expand_all: bool) -> None:
        self._populate_root_node_recursive(self.root)
        if expand_all:
            for node in self._get_current_nodes():
                node.expand()
        else:
            for node in self._get_current_nodes():
                node.collapse()

    def watch_unchanged(self, unchanged: bool) -> None:
        self.notify("unchanged changed to " + str(unchanged))
