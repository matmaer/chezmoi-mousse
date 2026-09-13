from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.reactive import reactive
from textual.widgets import Tree

from chezmoi_mousse import path_funcs, store
from chezmoi_mousse.str_enums import (
    BtnLabel,
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
    from chezmoi_mousse.data_classes import StatusByColumn
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

    @property
    def paths(self) -> StatusByColumn:
        return (
            store.cm_paths_legacy.apply
            if self.app_ids.tab_label == BtnLabel.apply
            else store.cm_paths_legacy.re_add
        )

    def _populate_unmanaged_nodes(self) -> None:
        expanded_dirs = [store.cfg.dest_dir]
        expanded_dirs += [
            node.data for node in self._iter_tree_nodes() if node.allow_expand
        ]

    def _iter_tree_nodes(self) -> Iterator[TreeNode[Path]]:
        queue: deque[TreeNode[Path]] = deque([self.root])
        while queue:
            node = queue.popleft()
            yield node
            queue.extend(node.children)

    def _get_tree_node(self, path: Path) -> TreeNode[Path] | None:
        for node in self._iter_tree_nodes():
            if node.data == path:
                return node
        return None

    def update_tree(self) -> None:

        # We update the tree based on the following available paths in store.py
        # - store.cm_paths_legacy.changes.managed_dirs.removed
        # - store.cm_paths_legacy.changes.managed_files.removed
        # - store.cm_paths_legacy.changes.managed_dirs.added
        # - store.cm_paths_legacy.changes.managed_files.added

        # -----------------
        # PHASE 1: REMOVALS
        # -----------------

        # 1.1 call .remove_children() on all top level removed directories
        top_removed_dirs: list[Path] = path_funcs.get_top_parents(
            store.cm_paths_legacy.changes.managed_dirs.removed
        )
        for d in top_removed_dirs:
            tree_node = self._get_tree_node(d)
            if tree_node is None:
                continue
            tree_node.remove_children()

        # 1.2 call .remove() on the top level removed directories themselves
        for d in top_removed_dirs:
            tree_node = self._get_tree_node(d)
            if tree_node is None:
                continue
            tree_node.remove()

        # 1.3 call .remove() on the file nodes which should still exist in the tree
        file_paths_to_remove = [
            f
            for f in store.cm_paths_legacy.changes.managed_files.removed
            if f not in top_removed_dirs
        ]
        for f in file_paths_to_remove:
            tree_node = self._get_tree_node(f)
            if tree_node is None:
                continue
            tree_node.remove()

        # ------------------
        # PHASE 2: ADDITIONS
        # ------------------

        # 2.1 the directories to be added depend on the context, we add all directories
        # with a status plus all n_dirs, which are context dependent!
        for d in self.paths.n_dirs | set(self.paths.status_dirs):
            if d.parent == store.cfg.dest_dir:
                parent_node = self.root
            else:
                parent_node = self._get_tree_node(d.parent)
            if parent_node is None:
                continue
            parent_node.add(f"{d.name}")

        # 2.2 add new managed files
        for f in self.paths.status_files:
            if f.parent == store.cfg.dest_dir:
                parent_node = self.root
            else:
                parent_node = self._get_tree_node(f.parent)
            if parent_node is None:
                continue
            parent_node.add_leaf(f"{f.name}")

        # -------------------------------------------------------------
        # PHASE 3: MODIFICATIONS (Cosmetic updates on existing nodes)
        # -------------------------------------------------------------
        # to change colors for paths with a changed status

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
            for node in self._iter_tree_nodes():
                if node.allow_expand:
                    node.expand()
        else:
            for node in self._iter_tree_nodes():
                if node is self.root:
                    continue
                if node.allow_expand:
                    node.expand()
                else:
                    node.collapse()
