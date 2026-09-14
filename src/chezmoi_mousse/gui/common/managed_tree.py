from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.reactive import reactive
from textual.widgets import Tree

from chezmoi_mousse import store
from chezmoi_mousse.str_enums import (
    Chars,
    ChezmoiStatusCode as CmSc,
    ColorVar,
    Tcss,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from textual import getters
    from textual.widgets.tree import TreeNode

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.gui.textual_app import ChezmoiGui


__all__ = ["ManagedTree"]


class ManagedTree(Tree[Path]):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded

    show_unchanged: reactive[bool] = reactive(False, init=False)
    show_unmanaged: reactive[bool] = reactive(False, init=False)
    expand_all: reactive[bool] = reactive(False, init=False)

    def __init__(self, app_ids: AppIds) -> None:
        self.app_ids = app_ids
        super().__init__(
            label=str(store.cfg.dest_dir),
            id=app_ids.managed_tree,
            classes=Tcss.managed_tree,
            data=store.cfg.dest_dir,
        )

    def on_mount(self) -> None:
        self.guide_depth: int = 3
        self.status_color: dict[CmSc | str, ColorVar] = {
            CmSc.Added: ColorVar.text_success,
            CmSc.Deleted: ColorVar.text_error,
            CmSc.Modified: ColorVar.text_warning,
            CmSc.N_DIR: ColorVar.text_secondary,
            CmSc.Run: ColorVar.bogus,
            CmSc.Space: ColorVar.dimmed,
            "unmanaged": ColorVar.text_error_dark,
        }
        self.root.expand()
        self.cached_tree_nodes: dict[Path, TreeNode[Path]] = {}

    def _populate_unmanaged_nodes(self) -> None: ...

    @property
    def _tree_node_iterator(self) -> Iterator[TreeNode[Path]]:
        queue: deque[TreeNode[Path]] = deque([self.root])
        while queue:
            node = queue.popleft()
            yield node
            queue.extend(node.children)

    def _get_tree_node(self, path: Path, cached: bool) -> TreeNode[Path] | None:
        if path == store.cfg.dest_dir:
            return self.root
        elif cached is True and path in self.cached_tree_nodes:
            return self.cached_tree_nodes[path]
        elif path in self.cached_tree_nodes:
            # If we don't ask cached remove it if it exists
            _ = self.cached_tree_nodes.pop(path)

        for node in self._tree_node_iterator:
            if node.data == path:
                found_node = node
                self.cached_tree_nodes[path] = found_node
                return found_node

    def insert_dir_node(self, parent_node: TreeNode[Path], path: Path) -> None:
        parent_dir_children = [
            child for child in parent_node.children if child.allow_expand
        ]
        # now determine the correct position to insert the new directory
        insert_index = 0
        for i, child in enumerate(parent_dir_children):
            if path.name < str(child.label):
                insert_index = i
                break
            insert_index = i + 1
        parent_node.add(f"{path.name}", before=insert_index)

    def insert_file_node(self, parent_node: TreeNode[Path], path: Path) -> None:
        parent_file_children = [
            child for child in parent_node.children if not child.allow_expand
        ]
        # now determine the correct position to insert the new directory
        insert_index = 0
        for i, child in enumerate(parent_file_children):
            if path.name < str(child.label):
                insert_index = i
                break
            insert_index = i + 1
        parent_node.add(f"{path.name}", before=insert_index)

    # #################################
    # # Watchers and message handling #
    # #################################

    @on(Tree.NodeCollapsed)
    def handle_node_collapsed(self, event: Tree.NodeCollapsed[Path]) -> None:
        if event.node is self.root:
            event.node.expand()

    @on(Tree.NodeExpanded)
    def handle_node_expanded(self, _: Tree.NodeExpanded[Path]) -> None: ...

    @on(Tree.NodeSelected)
    def send_node_context_message(self, event: Tree.NodeSelected[Path]) -> None:
        if event.node.data == store.cfg.dest_dir:
            return
        if event.node.data is None:
            return

    def watch_expand_all(self, expand_all: bool) -> None:
        if expand_all:
            for node in self._tree_node_iterator:
                if node.allow_expand:
                    node.expand()
        else:
            for node in self._tree_node_iterator:
                if node is self.root:
                    continue
                if node.allow_expand:
                    node.expand()
                else:
                    node.collapse()
