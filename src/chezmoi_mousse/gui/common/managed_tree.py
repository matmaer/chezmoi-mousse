from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING

from textual import getters, on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Label, Tree
from textual.widgets.tree import TreeNode

from chezmoi_mousse.enum_data import OpBtnEnum
from chezmoi_mousse.str_enums import Chars, TabLabel, Tcss

if TYPE_CHECKING:

    from chezmoi_mousse.cm_types import AppIds, ChezmoiGui

from .actionables import OpButton
from .messages import CurrentNodeMsg

__all__ = ["ManagedTree", "DestDirTree"]


class DestDirTree(Vertical):

    def __init__(self, ids: "AppIds") -> None:
        self.app_ids = ids
        super().__init__(id=ids.container.left_side, classes=Tcss.tab_left_vertical)

    def compose(self) -> ComposeResult:
        yield Label("destDir tree", classes=Tcss.dest_dir_tree_label)
        yield ManagedTree(tree_ids=self.app_ids)
        yield OpButton(
            btn_enum=OpBtnEnum.refresh_tree,
            btn_id=self.app_ids.op_btn.refresh_tree,
            app_ids=self.app_ids,
        )


class ManagedTree(Tree[Path]):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded

    show_unchanged: reactive[bool] = reactive(False, init=False)
    show_unmanaged: reactive[bool] = reactive(False, init=False)
    expand_all: reactive[bool] = reactive(False, init=False)

    def __init__(self, *, tree_ids: "AppIds") -> None:
        self.tree_ids = tree_ids
        super().__init__(label="", id=tree_ids.managed_tree, classes=Tcss.managed_tree)

    @property
    def tree_status_dirs(self) -> frozenset[Path]:
        return (
            self.app.cmattr.paths.apply_tree_status_dirs
            if self.tree_ids.tab_label == TabLabel.apply
            else self.app.cmattr.paths.re_add_tree_status_dirs
        )

    @property
    def status_files(self) -> frozenset[Path]:
        return (
            self.app.cmattr.paths.apply_status_files
            if self.tree_ids.tab_label == TabLabel.apply
            else self.app.cmattr.paths.re_add_status_files
        )

    def on_mount(self) -> None:
        self.guide_depth: int = 3
        self.configure_root_node()
        # keep state
        self.visible_dirs: set[TreeNode[Path]] = set()
        self.visible_files: set[TreeNode[Path]] = set()

    def configure_root_node(self) -> None:
        self.root.data = self.app.cmattr.dest_dir
        color = self.app.theme_variables["text-primary"]
        self.root.label = f"[{color} bold]{self.app.cmattr.dest_dir.name}[/]"
        self.root.expand()
        self.root.allow_expand = False  # prevent from being collapsed

    def all_nodes_bfs(self) -> set[TreeNode[Path]]:
        # BFS (Breadth-First Search) approach using deque for O(1) pops from the left.
        queue = deque(self.root.children)  # Start with the root's children
        node_set: set[TreeNode[Path]] = set()
        while queue:
            node = queue.popleft()
            node_set.add(node)
            queue.extend(node.children)
        return node_set

    def update_visible_nodes(self) -> None:
        # a node can be expanded but its parent may be collapsed so filter these out
        all_nodes = self.all_nodes_bfs()
        self.visible_dirs = {
            n for n in all_nodes if n.parent is not None and n.parent.is_expanded
        }
        self.visible_files = {n for n in all_nodes if n.parent in self.visible_dirs}

    def get_node_by_path(self, path: Path) -> TreeNode[Path]:
        return next((n for n in self.all_nodes_bfs() if n.data == path), self.root)

    def initial_tree_population(self) -> None:
        self.root.remove_children()
        self.populate_root_node_bfs()

        # expand all switch is false by default
        self.root.collapse_all()
        self.root.expand()

    def _add_or_expand_parents(self, path: Path) -> None:
        # don't add parents for these conditions
        if (
            path.parent == self.root.data
            or path.parent in self.app.cmattr.dest_dir.parents
        ):
            return

        # Add or expand potentially missing parent nodes
        # reversed makes sure we start with the highest level path
        for parent_path in reversed(path.parents):
            parent_node = self.get_node_by_path(parent_path)
            if parent_node.is_collapsed:
                parent_node.expand()
                continue
            else:
                # add missing parent path
                self._insert_node(parent_path, parent_node)
        self.update_visible_nodes()

    def show_requested_node(self, path: Path) -> None:
        self._add_or_expand_parents(path)
        node_parent = self.get_node_by_path(path.parent)
        node_parent.expand()
        new_node = self._insert_node(path, node_parent)
        if new_node is not None:
            self.select_node(new_node)

    def _insert_node(
        self, path: Path, parent_node: TreeNode[Path]
    ) -> TreeNode[Path] | None:
        if path == self.root.data or path in self.app.cmattr.dest_dir.parents:
            return None

        existing_node = next((n for n in self.all_nodes_bfs() if n.data == path), None)
        if existing_node is not None:
            return existing_node

        before_node = next(
            (
                n
                for n in parent_node.children
                if n.data is not None and n.data.name.lower() > path.name.lower()
            ),
            None,
        )
        if path in self.app.cmattr.paths.managed_files:
            return parent_node.add_leaf(path.name, data=path, before=before_node)
        return parent_node.add(path.name, data=path, before=before_node)

    def populate_root_node_bfs(self) -> None:
        dir_queue: deque[TreeNode[Path]] = deque([self.root])
        remaining_dirs = set(self.tree_status_dirs)

        while dir_queue and remaining_dirs:
            parent_node = dir_queue.popleft()
            parent_path = parent_node.data
            if parent_path is None:
                continue

            child_dirs = sorted(
                (path for path in remaining_dirs if path.parent == parent_path),
                key=lambda path: path.name.lower(),
            )
            for child_dir in child_dirs:
                child_node = self._insert_node(child_dir, parent_node)
                if child_node is not None:
                    dir_queue.append(child_node)
                remaining_dirs.remove(child_dir)

        file_queue: deque[TreeNode[Path]] = deque([self.root])
        remaining_files = set(self.status_files)

        while file_queue and remaining_files:
            parent_node = file_queue.popleft()
            parent_path = parent_node.data
            if parent_path is None:
                continue

            file_queue.extend(
                child
                for child in parent_node.children
                if child.data is not None and child.data in self.tree_status_dirs
            )
            child_files = sorted(
                (path for path in remaining_files if path.parent == parent_path),
                key=lambda path: path.name.lower(),
            )
            for child_file in child_files:
                self._insert_node(child_file, parent_node)
                remaining_files.remove(child_file)

    #################################
    # Watchers and message handling #
    #################################

    @on(Tree.NodeCollapsed)
    def update_collapsed(self) -> None:
        self.update_visible_nodes()

    @on(Tree.NodeExpanded)
    def update_expanded(self) -> None:
        if not self.expand_all:
            self.update_visible_nodes()

    @on(Tree.NodeSelected)
    def send_node_context_message(self, event: Tree.NodeSelected[Path]) -> None:
        if event.node.data is not None:
            self.post_message(CurrentNodeMsg(path=event.node.data, ids=self.tree_ids))

    def watch_show_unchanged(self, show_unchanged: bool) -> None:
        _ = show_unchanged
        return  # will be implemented later on

    def watch_expand_all(self, expand_all: bool) -> None:
        if expand_all is True:
            self.root.expand_all()
