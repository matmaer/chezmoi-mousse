from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from textual import getters, on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Label, Tree
from textual.widgets.tree import TreeNode

from chezmoi_mousse.enum_data import OpBtnEnum
from chezmoi_mousse.str_enums import Chars, Tcss

if TYPE_CHECKING:

    from chezmoi_mousse.cm_types import AppIds, ChezmoiGui

from .actionables import OpButton
from .messages import CurrentNodeMsg

__all__ = ["ManagedTree", "DestDirTree"]


@dataclass
class TreeState:
    # We keep track of the nodes to efficiently update the tree when changing the
    # filter switches, or after a chezmoi operation was performed and the managed paths
    # or status paths have changed. We will only store managed nodes here as we don't
    # know if unmananged paths have changed on disk, the will always be dynamically
    # added or removed to the tree when the switch changes.
    nodes: set[TreeNode[Path]] = field(default_factory=lambda: set())

    @property
    def expanded_nodes(self) -> set[TreeNode[Path]]:
        return {node for node in self.nodes if node.is_expanded}

    @property
    def expanded_paths(self) -> set[Path]:
        return {n.data for n in self.nodes if n.is_expanded and n.data is not None}

    # we always add file nodes by calling .add_leaf, and dir nodes by calling .add_node
    # so we can rely on .allow_expand

    @property
    def dir_nodes(self) -> set[TreeNode[Path]]:
        return {n for n in self.nodes if n.allow_expand}

    @property
    def file_nodes(self) -> set[TreeNode[Path]]:
        return {n for n in self.nodes if not n.allow_expand}

    @property
    def dir_paths(self) -> set[Path]:
        return {n.data for n in self.nodes if n.allow_expand and n.data is not None}

    @property
    def file_paths(self) -> set[Path]:
        return {n.data for n in self.nodes if not n.allow_expand and n.data is not None}

    @property
    def node_paths(self) -> set[Path]:
        return {n.data for n in self.nodes if n.data is not None}

    def get_node_by_path(self, path: Path) -> TreeNode[Path] | None:
        return next((n for n in self.nodes if n.data == path), None)


class DestDirTree(Vertical):

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


class ManagedTree(Tree[Path]):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded

    show_unchanged: reactive[bool] = reactive(False, init=False)
    show_unmanaged_files: reactive[bool] = reactive(False, init=False)
    expand_all: reactive[bool] = reactive(False, init=False)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(label="", id=ids.managed_tree, classes=Tcss.managed_tree)
        self.ids = ids
        self.guide_depth: int = 3
        self._tree_state = TreeState(nodes=set())

    def _update_tree_state(self, node_set: set[TreeNode[Path]]) -> None:
        self._tree_state.nodes = node_set

    def _get_nodes_from_tree(self, update_tree_state: bool) -> set[TreeNode[Path]]:
        # BFS approach using deque for O(1) pops from the left.
        queue = deque(self.root.children)  # Start with the root's children
        node_list: list[TreeNode[Path]] = []
        while queue:
            node = queue.popleft()
            node_list.append(node)
            queue.extend(node.children)
        # as we collected all real nodes, we update the _tree_state var also
        node_set = set(node_list)
        if update_tree_state:
            self._tree_state.nodes = node_set
        return node_set

    def initial_tree_population(self) -> None:
        # configure root node
        self.root.data = self.app.cmattr.dest_dir
        color = self.app.theme_variables["text-primary"]
        self.root.label = f"[{color} bold]{self.app.cmattr.dest_dir.name}[/]"
        self.root.expand()

        # add the root node to the tree state
        self._tree_state.nodes.add(self.root)

        # add all status paths to the root node
        self._populate_root_node_recursive(self.root)

        # expand all switch is false by default
        self.root.collapse_all()
        self.root.expand()

        # prevent the root node from being collapsed in the future
        self.root.allow_expand = False

        # update the tree state
        self._get_nodes_from_tree(update_tree_state=True)

    def update_tree(self) -> None:
        # called after running chezmoi apply, re-add, destroy, forget or add
        current_nodes = self._get_nodes_from_tree(update_tree_state=False)
        for node in current_nodes:
            if (
                node.data in self.app.cmattr.changes.removed_paths
                and node.data not in self.app.cmattr.paths.managed_dirs
            ):
                node.remove_children()
                node.remove()
        current_nodes = self._get_nodes_from_tree(update_tree_state=False)
        for node in current_nodes:
            if node in current_nodes:
                node.remove()

    def _add_or_expand_parents(self, path: Path) -> None:
        # don't add parents for these conditions
        if (
            path.parent == self.root.data
            or path.parent in self.app.cmattr.dest_dir.parents
        ):
            return

        # Add or expand potentially missing parent nodes
        # reversed makes sure we start with the highest level path
        parents_added = False
        for parent_path in reversed(path.parents):
            parent_node = self._tree_state.get_node_by_path(parent_path)
            if parent_node is not None and parent_node.is_collapsed:
                parent_node.expand()
                continue
            # add missing parent path
            self._insert_node(parent_path)
            parents_added = True
        if parents_added:
            self._get_nodes_from_tree(update_tree_state=True)

    def show_requested_node(self, path: Path) -> None:
        node_to_show = self._tree_state.get_node_by_path(path)
        node_parent = self._tree_state.get_node_by_path(path)
        if node_to_show is not None and node_parent is not None:
            if node_parent.is_collapsed:
                node_parent.expand()
            self.select_node(node_to_show)
        else:
            self._add_or_expand_parents(path)
        new_node = self._insert_node(path)
        self.select_node(new_node)

    def _insert_node(self, path: Path) -> None:
        if (
            path == self.root.data
            or path in self.app.cmattr.dest_dir.parents
            or path in self._tree_state.node_paths
        ):
            return

        parent_node = self._tree_state.get_node_by_path(path.parent)
        if parent_node is None:
            msg = (
                f"Trying to insert a node with path {path} into a non existing parent: "
                f"{path.parent}"
            )
            raise ValueError(msg)

        node_label = "placeholder"
        before_node = next(
            (
                n
                for n in parent_node.children
                if n.data is not None and n.data.name.lower() > path.name.lower()
            ),
            None,
        )
        if path in self.app.cmattr.paths.managed_files or path.is_file():
            parent_node.add_leaf(node_label, data=path, before=before_node)
        else:
            parent_node.add(node_label, data=path, before=before_node)

    def _populate_root_node_recursive(self, tree_node: TreeNode[Path]) -> None:
        if tree_node.data is None:
            raise ValueError("tree_node.data is None in _populate_node")

    #################################
    # Watchers and message handling #
    #################################

    @on(Tree.NodeCollapsed)
    def update_collapsed(self, event: Tree.NodeCollapsed[Path]) -> None:
        if event.node.data is None:
            return

    @on(Tree.NodeExpanded)
    def update_expanded(self, event: Tree.NodeExpanded[Path]) -> None:
        if not self.expand_all:
            self._tree_state.nodes.discard(event.node)
        elif self.show_unchanged:
            ...

    @on(Tree.NodeSelected)
    def send_node_context_message(self, event: Tree.NodeSelected[Path]) -> None:
        if event.node.data is not None:
            self.post_message(CurrentNodeMsg(path=event.node.data, ids=self.ids))

    def watch_show_unchanged(self, show_unchanged: bool) -> None:
        if show_unchanged is True:
            self._populate_root_node_recursive(self.root)
        if self.expand_all:
            self.root.expand_all()

    def watch_show_unmanaged_files(self, show_unmanaged: bool) -> None:
        if show_unmanaged is True:
            self._populate_root_node_recursive(self.root)

    def watch_expand_all(self, expand_all: bool) -> None:
        if expand_all is True:
            self.root.expand_all()
