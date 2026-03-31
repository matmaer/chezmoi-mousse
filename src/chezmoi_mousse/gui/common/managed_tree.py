from collections import deque
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

__all__ = ["ManagedTree", "DestDirTree"]


class DestDirTree(Vertical, AppType):

    def __init__(self, ids: "AppIds"):
        super().__init__(id=ids.container.left_side, classes=Tcss.tab_left_vertical)
        self.ids = ids

    def compose(self) -> ComposeResult:
        yield Label("destDir tree", classes=Tcss.dest_dir_tree_label)
        yield ManagedTree(self.ids)
        yield OpButton(
            btn_enum=OpBtnEnum.refresh_tree,
            btn_id=self.ids.op_btn.refresh_tree,
            app_ids=self.ids,
        )

    def on_mount(self) -> None:
        refresh_btn = self.query_one(self.ids.op_btn.refresh_tree_q, OpButton)
        refresh_btn.remove_class(Tcss.operate_button)
        refresh_btn.add_class(Tcss.refresh_button)


class ManagedTree(Tree[Path], AppType):

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded

    unchanged: reactive[bool] = reactive(False, init=False)
    expand_all: reactive[bool] = reactive(False, init=False)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(label="", id=ids.managed_tree, classes=Tcss.managed_tree)
        self.guide_depth: int = 3
        self.ids = ids

    def on_mount(self) -> None:
        self._first_time_populating = True
        self._expanded_backup: set[TreeNode[Path]] = set()

    def _get_nodes(self) -> set[TreeNode[Path]]:
        # BFS approach using deque for O(1) pops from the left.
        queue = deque([self.root])
        visited: list[TreeNode[Path]] = []
        while queue:
            node = queue.popleft()
            visited.append(node)
            queue.extend(node.children)
        return set(visited)

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
            current_nodes = self._get_nodes()
            for node in current_nodes:
                if (
                    node.data != CMD.cache.dest_dir
                    and node.data in CMD.cache.sets.managed_dirs
                ):
                    node.collapse()
            self._first_time_populating = False
        self._expanded_backup = self._get_nodes(expanded=True)
        self.select_node(self.root)

    def select_node_by_path(self, path: Path) -> None:
        current_nodes = self._get_nodes()
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
        n_dirs_in = CMD.cache.sets.n_dirs_in(tree_node.data)
        status_dirs_in = CMD.cache.sets.status_dirs_in(tree_node.data)

        for dir in sorted(n_dirs_in | status_dirs_in):
            child_node = self._insert_dir(tree_node, dir)
            if child_node is None:
                continue
            self._populate_root_node_recursive(child_node)

        # TODO: Double check if Python runs this code on all previous recursed function
        # calls, which seems to be the case and what we want.
        file_paths_in = sorted(CMD.cache.sets.status_files_in(tree_node.data))
        for file_path in reversed(file_paths_in):
            self._insert_file(tree_node, file_path)

    #################################
    # Watchers and message handling #
    #################################

    @on(Tree.NodeCollapsed)
    def remove_from_expanded_backup(self, event: Tree.NodeCollapsed[Path]) -> None:
        if not self.expand_all:
            self._expanded_backup.discard(event.node)
        if self.unchanged:
            self.watch_unchanged(self.unchanged)

    @on(Tree.NodeExpanded)
    def update_after_expand(self, event: Tree.NodeExpanded[Path]) -> None:
        if not self.expand_all:
            self._expanded_backup.add(event.node)
        if self.unchanged:
            self.watch_unchanged(self.unchanged)

    @on(Tree.NodeSelected)
    def send_node_context_message(self, event: Tree.NodeSelected[Path]) -> None:
        if event.node.data is None:
            raise ValueError("event.node.data is None in send_node_context")
        if self.ids.canvas_name == TabLabel.apply:
            self.post_message(CurrentApplyNodeMsg(event.node.data))
        elif self.ids.canvas_name == TabLabel.re_add:
            self.post_message(CurrentReAddNodeMsg(event.node.data))

    def watch_expand_all(self, expand_all: bool) -> None:
        if expand_all is True:
            self._expanded_backup = self._get_nodes(expanded=True)
            self.root.expand_all()
        elif expand_all is False:
            current_nodes = self._get_nodes()
            for node in current_nodes:
                if node not in self._expanded_backup:
                    node.collapse()

    def watch_unchanged(self, unchanged: bool) -> None:

        current_nodes = self._get_nodes()

        if unchanged is True:
            for path in CMD.cache.sets.tree_x_dirs:
                parent_node = next(
                    (n for n in current_nodes if n.data == path.parent), None
                )
                if parent_node is not None:
                    self._insert_dir(parent_node, path)
            for path in CMD.cache.sets.x_files:
                parent_node = next(
                    (n for n in current_nodes if n.data == path.parent), None
                )
                if parent_node is not None:
                    self._insert_file(parent_node, path)
        elif unchanged is False:
            for node in self._get_nodes(x_nodes=True):
                node.remove()
