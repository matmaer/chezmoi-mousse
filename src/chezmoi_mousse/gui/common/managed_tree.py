from __future__ import annotations

from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from textual import getters, on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Label, Tree
from textual.widgets.tree import TreeNode

from chezmoi_mousse.functions import CheckPath
from chezmoi_mousse.named_tuples import ManagedTreePaths
from chezmoi_mousse.str_enums import (
    Chars,
    ColorVar,
    PathKind,
    StatusCode,
    TabLabel,
    Tcss,
)

if TYPE_CHECKING:

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.cm_types import ScanDirResult, TreeNodeDict
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

from .actionables import RefreshTreeButton
from .messages import CurrentNodeMsg

__all__ = ["ManagedTree", "DestDirTree"]


class DestDirTree(Vertical):

    def __init__(self, ids: AppIds) -> None:
        self.app_ids = ids
        super().__init__(id=ids.container.left_side, classes=Tcss.tab_left_vertical)

    def compose(self) -> ComposeResult:
        yield Label("destDir tree", classes=Tcss.dest_dir_tree_label)
        yield ManagedTree(self.app_ids)
        yield RefreshTreeButton(self.app_ids)


@dataclass(slots=True)
class ManagedTreeState:
    root_node: TreeNode[Path]
    selected_node: TreeNode[Path]
    selected_path: Path | None = None  # Track selected path instead of stale TreeNode
    expanded_paths: set[Path] = field(default_factory=lambda: set())
    show_unchanged: bool = False
    show_unmanaged: bool = False
    expand_all: bool = False


@dataclass(slots=True)
class TreeDiff:
    removed_managed: set[Path] = field(default_factory=lambda: set())
    added_managed: set[Path] = field(default_factory=lambda: set())
    changed_status: dict[Path, tuple[StatusCode | None, StatusCode | None]] = field(
        default_factory=lambda: {}
    )


@dataclass(slots=True)
class TreeSnapshot:
    managed_paths: set[Path] = field(default_factory=lambda: set())
    status_map: dict[Path, StatusCode] = field(default_factory=lambda: {})

    def diff_against(self, new_snapshot: TreeSnapshot) -> TreeDiff:
        """Calculates the changes between the current snapshot and a new snapshot."""
        removed_managed = self.managed_paths - new_snapshot.managed_paths
        added_managed = new_snapshot.managed_paths - self.managed_paths

        changed_status: dict[Path, tuple[StatusCode | None, StatusCode | None]] = {}
        retained = self.managed_paths & new_snapshot.managed_paths

        for path in retained:
            old_code = self.status_map.get(path)
            new_code = new_snapshot.status_map.get(path)
            if old_code != new_code:
                changed_status[path] = (old_code, new_code)

        return TreeDiff(
            removed_managed=removed_managed,
            added_managed=added_managed,
            changed_status=changed_status,
        )


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
        super().__init__(label="", id=app_ids.managed_tree, classes=Tcss.managed_tree)

    def on_mount(self) -> None:
        self.guide_depth: int = 3

        # configure root node
        self.root.data = self.app.cmattr.dest_dir
        color = self.app.get_color(ColorVar.text_primary)
        self.root.label = f"[{color}]{self.app.cmattr.dest_dir.name}[/]"
        self.root.expand()
        self.root.allow_expand = False
        self.select_node(self.root)

        self.status_color: dict[StatusCode | PathKind, ColorVar] = {
            StatusCode.Added: ColorVar.text_success,
            StatusCode.Deleted: ColorVar.text_error,
            StatusCode.Modified: ColorVar.text_warning,
            StatusCode.N_DIR: ColorVar.text_secondary,
            StatusCode.Run: ColorVar.bogus,
            StatusCode.Space: ColorVar.dimmed,
            PathKind.UNMANAGED: ColorVar.text_error_dark,
        }
        self.state = ManagedTreeState(
            root_node=self.root, selected_node=self.root, selected_path=self.root.data
        )
        if self.root.data:
            self.state.expanded_paths.add(self.root.data)

    @property
    def paths(self) -> ManagedTreePaths:
        return (
            self.app.cmattr.paths.apply_tree_paths
            if self.app_ids.tab_label == TabLabel.apply
            else self.app.cmattr.paths.re_add_tree_paths
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
                color = self.app.get_color(ColorVar.ready)
            elif status_code is not None:
                color = self.app.get_color(self.status_color[status_code])
            else:
                color = self.app.get_color(ColorVar.dimmed)

            italic = " italic" if managed_kind == PathKind.EXISTS_FALSE else ""
            return f"[{color}{italic}]{node_path.name}[/]"

        tree_node = self._get_tree_node(path, parent_node=False)
        if tree_node is not None:
            return tree_node

        managed_kind = (
            self.paths.managed_dirs.get(path, None)
            if dir_node
            else self.paths.managed_files.get(path, None)
        )
        status_code = (
            self.paths.tree_status_dirs.get(path, None)
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
        for path in self.paths.unchanged_tree_dirs:
            parent_node = self._get_tree_node(path, parent_node=True)
            if parent_node is not None:
                self._insert_node(dir_node=True, path=path, parent_node=parent_node)

        for path in self.paths.unchanged_files:
            parent_node = self._get_tree_node(path, parent_node=True)
            if parent_node is not None:
                self._insert_node(dir_node=False, path=path, parent_node=parent_node)

    def _populate_unmanaged_nodes(self) -> None:
        expanded_dirs = [self.paths.dest_dir]
        expanded_dirs += [
            node.data
            for node in self._iter_tree_nodes()
            if node.allow_expand and node.data in self.state.expanded_paths
        ]

        for dir_path in expanded_dirs:
            unmanaged: ScanDirResult = CheckPath.os_scan_dir(dir_path, managed_dir=True)
            if isinstance(unmanaged, PathKind):
                continue

            for item in unmanaged:
                if (
                    item.path in self.paths.managed_dirs
                    or item.path in self.paths.managed_files
                ):
                    continue

                if not self.show_unchanged and (
                    item.path in self.paths.unchanged_tree_dirs
                    or item.path in self.paths.unchanged_files
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

    def get_current_snapshot(self) -> TreeSnapshot:
        """Returns a snapshot of current managed paths and statuses prior to an
        operation."""
        managed_paths = set(self.paths.managed_dirs | self.paths.managed_files)
        status_map = {**self.paths.tree_status_dirs, **self.paths.status_files}
        return TreeSnapshot(managed_paths=managed_paths, status_map=status_map)

    def update_tree(self) -> None:
        """Rebuilds the tree structure from current chezmoi paths and restores state."""
        self.root.remove_children()

        # Add status directories and files to root node
        nodes_by_path: TreeNodeDict = {self.paths.dest_dir: self.root}

        for path in self.paths.tree_status_dirs:
            parent_node = nodes_by_path.get(path.parent, self.root)
            node: TreeNode[Path] = self._insert_node(
                dir_node=True, path=path, parent_node=parent_node
            )
            nodes_by_path[path] = node

        for file_path in self.paths.status_files:
            parent_node = nodes_by_path.get(file_path.parent, self.root)
            self._insert_node(dir_node=False, path=file_path, parent_node=parent_node)

        # Re-populate optional active views (unchanged / unmanaged)
        if self.show_unchanged:
            self._populate_unchanged_nodes()

        if self.show_unmanaged:
            self._populate_unmanaged_nodes()

        # Restore directory expansions
        for node in self._iter_tree_nodes():
            if node is self.root:
                continue
            if node.allow_expand:
                if self.expand_all or (node.data in self.state.expanded_paths):
                    node.expand()
                else:
                    node.collapse()

        # Restore selection with parent fallback
        target_path = self.state.selected_path
        node_to_select: TreeNode[Path] | None = None

        while target_path is not None and target_path != self.root.data:
            node_to_select = self._get_tree_node(target_path, parent_node=False)
            if node_to_select is not None:
                break
            # If target node was deleted/removed, walk up to parent
            target_path = target_path.parent

        if node_to_select is not None:
            self.select_node(node_to_select)
        else:
            self.select_node(self.root)

    # #################################
    # # Watchers and message handling #
    # #################################

    @on(Tree.NodeCollapsed)
    def handle_node_collapsed(self, event: Tree.NodeCollapsed[Path]) -> None:
        if not self.expand_all and event.node.data:
            self.state.expanded_paths.discard(event.node.data)

    @on(Tree.NodeExpanded)
    def handle_node_expanded(self, event: Tree.NodeExpanded[Path]) -> None:
        if not self.expand_all and event.node.data:
            self.state.expanded_paths.add(event.node.data)

    @on(Tree.NodeSelected)
    def send_node_context_message(self, event: Tree.NodeSelected[Path]) -> None:
        self.state.selected_node = event.node
        if event.node.data is None:
            raise RuntimeError("Node data is None, which is unexpected.")

        self.state.selected_path = event.node.data

        is_unmanaged = (
            event.node.data not in self.paths.managed_dirs | self.paths.managed_files
            and event.node is not self.root
        )
        has_status = (
            event.node.data in self.paths.status_files
            or event.node.data in self.paths.status_dirs
        )
        is_n_dir = event.node.data in self.paths.n_dirs
        self.post_message(
            CurrentNodeMsg(
                ids=self.app_ids,
                path=event.node.data,
                no_changed_paths=self.paths.no_status_paths,
                has_status=has_status,
                is_n_dir=is_n_dir,
                dest_dir=self.paths.dest_dir,
                is_unmanaged=is_unmanaged,
            )
        )

    def watch_expand_all(self, expand_all: bool) -> None:
        self.state.expand_all = expand_all
        if expand_all:
            for node in self._iter_tree_nodes():
                if node.allow_expand:
                    node.expand()
        else:
            for node in self._iter_tree_nodes():
                if node is self.root:
                    continue
                if node.allow_expand:
                    if node.data in self.state.expanded_paths:
                        node.expand()
                    else:
                        node.collapse()

    def watch_show_unmanaged(self, show_unmanaged: bool) -> None:
        self.state.show_unmanaged = show_unmanaged
        if show_unmanaged:
            self._populate_unmanaged_nodes()
        else:
            for node in list(self._iter_tree_nodes()):
                if (
                    node.data not in self.paths.managed_dirs | self.paths.managed_files
                    and node is not self.root
                ):
                    node.remove()

    def watch_show_unchanged(self, show_unchanged: bool) -> None:
        self.state.show_unchanged = show_unchanged
        if show_unchanged:
            self._populate_unchanged_nodes()
        else:
            for path in self.paths.unchanged_tree_dirs:
                node = self._get_tree_node(path, parent_node=False)
                if node is not None:
                    node.remove()
            for path in self.paths.unchanged_files:
                node = self._get_tree_node(path, parent_node=False)
                if node is not None:
                    node.remove()
