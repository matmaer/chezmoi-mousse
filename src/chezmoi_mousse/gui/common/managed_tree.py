from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.reactive import reactive
from textual.widgets import Tree

from chezmoi_mousse import path_funcs, store
from chezmoi_mousse.gui.common.messages import CurrentNodeMsg
from chezmoi_mousse.str_enums import (
    BtnLabel,
    Chars,
    ColorVar,
    PathKind,
    StatusCode,
    Tcss,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from textual import getters
    from textual.widgets.tree import TreeNode

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.data_classes import StatusPaths
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
        self.status_color: dict[StatusCode | PathKind, ColorVar] = {
            StatusCode.Added: ColorVar.text_success,
            StatusCode.Deleted: ColorVar.text_error,
            StatusCode.Modified: ColorVar.text_warning,
            StatusCode.N_DIR: ColorVar.text_secondary,
            StatusCode.Run: ColorVar.bogus,
            StatusCode.Space: ColorVar.dimmed,
            PathKind.UNMANAGED: ColorVar.text_error_dark,
        }

    @property
    def paths(self) -> StatusPaths:
        return (
            store.paths.apply
            if self.app_ids.tab_label == BtnLabel.apply
            else store.paths.re_add
        )

    def _insert_node(
        self, dir_node: bool, path: Path, parent_node: TreeNode[Path]
    ) -> TreeNode[Path]:
        def _get_node_label(
            node_path: Path,
            managed_kind: PathKind | None,
            status_code: StatusCode | None,
        ) -> str:
            if managed_kind is None:
                color = self.app.theme_variables[ColorVar.accent_darken_2]
            elif status_code is not None:
                color = self.app.theme_variables[self.status_color[status_code]]
            else:
                color = self.app.theme_variables[ColorVar.dimmed]

            italic = " italic" if managed_kind == PathKind.MISSING else ""
            return f"[{color}{italic}]{node_path.name}[/]"

        tree_node = self._get_tree_node(path, parent_node=False)
        if tree_node is not None:
            return tree_node

        managed_kind = (
            store.paths.managed.dirs.get(path, None)
            if dir_node
            else store.paths.managed.files.get(path, None)
        )
        status_code = (
            self.paths.status_dirs.get(path, None)
            if dir_node
            else self.paths.status_files.get(path, None)
        )

        before = len(parent_node.children)

        for index, child in enumerate(parent_node.children):
            if child.data is None:
                raise RuntimeError("Child node data is None, which is unexpected.")

            if child.allow_expand != dir_node:
                if dir_node:
                    before = index
                    break
            elif child.data.name.lower() > path.name.lower():
                before = index
                break

        return parent_node.add(
            _get_node_label(path, managed_kind, status_code),
            data=path,
            before=before,
            allow_expand=dir_node,
        )

    def _populate_unchanged_nodes(self) -> None:
        for path in sorted(self.paths.no_status_dirs):
            parent_node = self._get_tree_node(path, parent_node=True)
            if parent_node is not None:
                self._insert_node(dir_node=True, path=path, parent_node=parent_node)

        for path in sorted(self.paths.no_status_files):
            parent_node = self._get_tree_node(path, parent_node=True)
            if parent_node is not None:
                self._insert_node(dir_node=False, path=path, parent_node=parent_node)

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

            for item in unmanaged:
                if item.path in store.paths.managed.dirs | store.paths.managed.files:
                    continue

                if not self.show_unchanged and (
                    item.path in store.paths.managed.space_paths
                ):
                    continue

                parent_node = self._get_tree_node(item.path, parent_node=True)
                if parent_node is not None:
                    self._insert_node(
                        dir_node=item.is_dir, path=item.path, parent_node=parent_node
                    )

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

    def update_tree(self) -> None:
        self.root.remove_children()

        # status_dirs already contains every ancestor dir needed to reach a
        # status path (as StatusCode.N_DIR), so sorting by depth guarantees
        # each parent node exists before its child is inserted.
        entries: deque[tuple[Path, bool]] = deque(
            sorted(
                [(path, True) for path in self.paths.status_dirs]
                + [(path, False) for path in self.paths.status_files],
                key=lambda entry: len(entry[0].parts),
            )
        )

        while entries:
            path, dir_node = entries.popleft()
            parent_node = self._get_tree_node(path, parent_node=True)
            if parent_node is None:
                raise RuntimeError(f"no parent node found to attach {path}")
            self._insert_node(dir_node=dir_node, path=path, parent_node=parent_node)

        if self.show_unchanged:
            self._populate_unchanged_nodes()
        if self.show_unmanaged:
            self._populate_unmanaged_nodes()

    # #################################
    # # Watchers and message handling #
    # #################################

    @on(Tree.NodeCollapsed)
    def handle_node_collapsed(self, event: Tree.NodeCollapsed[Path]) -> None:
        if event.node is self.root:
            event.node.expand()

    @on(Tree.NodeExpanded)
    def handle_node_expanded(self, event: Tree.NodeExpanded[Path]) -> None: ...

    @on(Tree.NodeSelected)
    def send_node_context_message(self, event: Tree.NodeSelected[Path]) -> None:
        if event.node.data == store.cfg.dest_dir:
            return
        has_status = event.node.data in self.paths.status_paths
        if event.node.data is None:
            return
        is_dest_dir = event.node is self.root
        is_unmanaged = event.node.data not in store.paths.managed.paths
        self.post_message(
            CurrentNodeMsg(
                app_ids=self.app_ids,
                path=event.node.data,
                has_status=has_status,
                is_dest_dir=is_dest_dir,
                is_unmanaged=is_unmanaged,
            )
        )

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

    def watch_show_unmanaged(self, show_unmanaged: bool) -> None:
        if show_unmanaged:
            self._populate_unmanaged_nodes()
        else:
            for node in list(self._iter_tree_nodes()):
                if node.data not in store.paths.managed.paths and node is not self.root:
                    node.remove()

    def watch_show_unchanged(self, show_unchanged: bool) -> None:
        if show_unchanged:
            self._populate_unchanged_nodes()
        else:
            for path in self.paths.ns_dirs:
                node = self._get_tree_node(path, parent_node=False)
                if node is not None:
                    node.remove()
            for path in self.paths.no_status_files:
                node = self._get_tree_node(path, parent_node=False)
                if node is not None:
                    node.remove()
