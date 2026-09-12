from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.reactive import reactive
from textual.widgets import Tree

from chezmoi_mousse import path_funcs, store
from chezmoi_mousse.str_enums import (
    Chars,
    ChezmoiStatusCode as CmSc,
    ColorVar,
    PathKind,
    Tcss,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from textual import getters
    from textual.widgets.tree import TreeNode

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.path_funcs import ScanDirResult


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
        self.status_color: dict[CmSc | PathKind, ColorVar] = {
            CmSc.Added: ColorVar.text_success,
            CmSc.Deleted: ColorVar.text_error,
            CmSc.Modified: ColorVar.text_warning,
            CmSc.N_DIR: ColorVar.text_secondary,
            CmSc.Run: ColorVar.bogus,
            CmSc.Space: ColorVar.dimmed,
            PathKind.UNMANAGED: ColorVar.text_error_dark,
        }

    def _populate_unmanaged_nodes(self) -> None:
        expanded_dirs = [store.cfg.dest_dir]
        expanded_dirs += [
            node.data for node in self._iter_tree_nodes() if node.allow_expand
        ]

        for dir_path in expanded_dirs:
            if dir_path is None:
                return
            unmanaged: ScanDirResult = path_funcs.os_scan_dir(dir_path)
            if isinstance(unmanaged, PathKind):
                continue

    def _iter_tree_nodes(self) -> Iterator[TreeNode[Path]]:
        queue: deque[TreeNode[Path]] = deque([self.root])
        while queue:
            node = queue.popleft()
            yield node
            queue.extend(node.children)

    def _get_tree_node(
        self, path: Path | None, *, parent_node: bool
    ) -> TreeNode[Path] | None:
        if path is None:
            return None
        target_path = path.parent if parent_node else path
        for node in self._iter_tree_nodes():
            if node.data == target_path:
                return node
        return None

    def update_tree(self) -> None: ...

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
