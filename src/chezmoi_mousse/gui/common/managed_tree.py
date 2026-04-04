from collections import deque
from dataclasses import dataclass, field
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


@dataclass
class TreeNodesBackup:
    all_nodes: set[TreeNode[Path]]
    expanded: set[TreeNode[Path]] = field(init=False)

    def __post_init__(self) -> None:
        self.expanded = {node for node in self.all_nodes if node.is_expanded}


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
        self.ids = ids
        self.guide_depth: int = 3
        self._nodes_backup = TreeNodesBackup(all_nodes=set())

    def on_mount(self) -> None:
        self._config_root_node()
        self._first_time_populating = True

    def _config_root_node(self) -> None:
        self.root.data = CMD.cache.dest_dir
        color = self.app.theme_variables["text-primary"]
        self.root.label = f"[{color} bold]{CMD.cache.dest_dir.name}[/]"
        self.root.expand()
        self.root.allow_expand = False  # to prevent the root node from being collapsed
        self.select_node(self.root)

    def _get_nodes(self) -> set[TreeNode[Path]]:
        # BFS approach using deque for O(1) pops from the left.
        queue = deque(self.root.children)  # Start with the root's children
        visited: list[TreeNode[Path]] = []
        while queue:
            node = queue.popleft()
            visited.append(node)
            queue.extend(node.children)
        return set(visited)

    def _get_node_by_path(self, path: Path) -> TreeNode[Path] | None:
        if path == CMD.cache.dest_dir:
            return self.root
        current_nodes = self._get_nodes()
        return next((n for n in current_nodes if n.data == path), None)

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
        self._config_root_node()
        self._populate_root_node_recursive(self.root)
        if self._first_time_populating:
            # expand all switch is false by default
            self.root.collapse_all()
            self.root.expand()
            self._first_time_populating = False
            self._nodes_backup = TreeNodesBackup(all_nodes=self._get_nodes())
            return
        if self.expand_all is True:
            self.root.expand_all()
        else:
            self._nodes_backup = TreeNodesBackup(all_nodes=self._get_nodes())

    def show_requested_node(self, path: Path) -> None:
        # Add potentially missing parent nodes or expand existing collapsed parent nodes
        for parent_path in path.parents:
            if (
                parent_path in CMD.cache.dest_dir.parents
                or parent_path == CMD.cache.dest_dir
            ):
                continue
            existing_parent = self._get_node_by_path(parent_path)
            if existing_parent is not None and existing_parent.is_collapsed is True:
                existing_parent.expand()
                continue
            new_node = self._insert_node(parent_path)
            if new_node is not None:
                new_node.expand()

        existing_node = self._get_node_by_path(path)
        if existing_node is not None:
            self.select_node(existing_node)
        else:
            new_node = self._insert_node(path)
            self.select_node(new_node)

    def _insert_node(self, path: Path) -> TreeNode[Path] | None:
        if path in CMD.cache.dest_dir.parents or path == CMD.cache.dest_dir:
            return None
        if self._get_node_by_path(path) is not None:
            return None
        parent_node = self._get_node_by_path(path.parent)
        if parent_node is None:
            raise ValueError(f"Parent node for {path} not found.")
        node_label = self._create_colored_label(path)
        if path in CMD.cache.sets.managed_dirs:
            before_node = next(
                (
                    n
                    for n in parent_node.children
                    if n.allow_expand
                    and n.data is not None
                    and n.data.name.lower() > path.name.lower()
                ),
                None,
            )
            if before_node is None:
                before_node = next(
                    (n for n in parent_node.children if not n.allow_expand), None
                )
            return parent_node.add(node_label, data=path, before=before_node)
        elif path in CMD.cache.sets.managed_files:
            before_node = next(
                (
                    n
                    for n in parent_node.children
                    if not n.allow_expand
                    and n.data is not None
                    and n.data.name.lower() > path.name.lower()
                ),
                None,
            )
            return parent_node.add_leaf(node_label, data=path, before=before_node)
        else:
            return None

    def _populate_root_node_recursive(self, tree_node: TreeNode[Path]) -> None:
        if tree_node.data is None:
            raise ValueError("tree_node.data is None in _populate_node")
        n_dirs_in = CMD.cache.sets.n_dirs_in(tree_node.data)
        status_dirs_in = CMD.cache.sets.status_dirs_in(tree_node.data)
        tree_x_dirs_in = CMD.cache.sets.tree_x_dirs_in(tree_node.data)
        files_to_insert = CMD.cache.sets.status_files_in(tree_node.data)
        x_files_in = CMD.cache.sets.x_files_in(tree_node.data)

        dir_to_insert = n_dirs_in | status_dirs_in

        if self.unchanged:
            dir_to_insert |= tree_x_dirs_in
            files_to_insert = files_to_insert | x_files_in

        for dir in dir_to_insert:
            child_node = self._insert_node(dir)
            if child_node is None:
                continue
            self._populate_root_node_recursive(child_node)

        for file_path in files_to_insert:
            self._insert_node(file_path)

    #################################
    # Watchers and message handling #
    #################################

    @on(Tree.NodeCollapsed)
    @on(Tree.NodeExpanded)
    def update_nodes_backup(self) -> None:
        if not self.expand_all:
            self._nodes_backup = TreeNodesBackup(all_nodes=self._get_nodes())

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
            self._nodes_backup = TreeNodesBackup(all_nodes=self._get_nodes())
            self.root.expand_all()
        elif expand_all is False:
            current_nodes = self._get_nodes()
            for node in current_nodes:
                if node not in self._nodes_backup.expanded:
                    node.collapse()
            self._nodes_backup = TreeNodesBackup(all_nodes=self._get_nodes())

    def watch_unchanged(self, unchanged: bool) -> None:
        if unchanged is True:
            self._populate_root_node_recursive(self.root)
        elif unchanged is False:
            for dir_path in CMD.cache.sets.tree_x_dir_roots:
                node = self._get_node_by_path(dir_path)
                if node is not None:
                    node.remove()
            for file_path in CMD.cache.sets.x_files:
                node = self._get_node_by_path(file_path)
                if node is not None:
                    node.remove()
        if self.expand_all:
            self.root.expand_all()
