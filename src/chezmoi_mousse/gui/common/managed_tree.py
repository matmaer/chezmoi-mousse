from __future__ import annotations

from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass
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


@dataclass(slots=True, frozen=True)
class ManagedTreeState:
    root_node: TreeNode[Path]
    current_dir_nodes: TreeNodeDict
    current_file_nodes: TreeNodeDict
    selected_node: TreeNode[Path]
    show_unchanged: bool
    show_unmanaged: bool
    expand_all: bool


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
        color = self.app.theme_variables["text-primary"]
        self.root.label = f"[{color} bold]{self.app.cmattr.dest_dir.name}[/]"
        self.root.expand()
        self.root.allow_expand = False  # prevent from being collapsed when we select it

        self.status_color: dict[StatusCode | PathKind, ColorVar] = {
            StatusCode.Added: ColorVar.text_success,
            StatusCode.Deleted: ColorVar.text_error,
            StatusCode.Modified: ColorVar.text_warning,
            StatusCode.N_DIR: ColorVar.text_secondary,
            StatusCode.Run: ColorVar.bogus,
            StatusCode.Space: ColorVar.dimmed,
            PathKind.UNMANAGED: ColorVar.text_error_dark,
        }
        self.tree_snapshot: ManagedTreeState = self._snapshot_tree_state()

    @property
    def paths(self) -> ManagedTreePaths:
        return (
            self.app.cmattr.paths.apply_tree_paths
            if self.app_ids.tab_label == TabLabel.apply
            else self.app.cmattr.paths.re_add_tree_paths
        )

    def _iter_tree_nodes(self) -> Iterator[TreeNode[Path]]:
        queue: deque[TreeNode[Path]] = deque([self.root])
        while queue:
            node = queue.popleft()
            yield node
            queue.extend(node.children)

    def _get_tree_node(self, path: Path, *, parent_node: bool) -> TreeNode[Path] | None:
        for node in self._iter_tree_nodes():
            if parent_node:
                if node.data == path.parent:
                    return node
            else:
                if node.data == path:
                    return node
        return None

    def _snapshot_tree_state(self) -> ManagedTreeState:
        current_dir_nodes: TreeNodeDict = {}
        current_file_nodes: TreeNodeDict = {}
        selected_node = self.cursor_node if self.cursor_node is not None else self.root
        for node in self._iter_tree_nodes():
            if node.data is not None:
                if node.allow_expand and node.is_expanded:
                    current_dir_nodes[node.data] = node
                else:
                    current_file_nodes[node.data] = node
        return ManagedTreeState(
            root_node=self.root,
            current_dir_nodes=current_dir_nodes,
            current_file_nodes=current_file_nodes,
            selected_node=selected_node,
            show_unchanged=self.show_unchanged,
            show_unmanaged=self.show_unmanaged,
            expand_all=self.expand_all,
        )

    def _get_node_label(
        self,
        node_path: Path,
        managed_kind: PathKind | None,
        status_code: StatusCode | None,
    ) -> str:
        # determine the color for the node
        if managed_kind is None:
            color = self.app.get_color(ColorVar.ready)
        elif status_code is not None:
            color = self.app.get_color(self.status_color[status_code])
        else:
            color = self.app.get_color(ColorVar.dimmed)
        # determine if the label should be italic or not
        italic = ""
        if managed_kind == PathKind.EXISTS_FALSE:
            italic = " italic"
        return f"[{color}{italic}]{node_path.name}[/]"

    def update_tree(self) -> None:
        self.tree_snapshot = self._snapshot_tree_state()
        self._populate_tree_bfs()

    def _populate_tree_bfs(self) -> None:
        # Stores mapping of Path -> created tree node
        nodes_by_path: TreeNodeDict = {self.paths.dest_dir: self.root}

        # Add all directory nodes
        for path in self.paths.tree_status_dirs:
            parent_node = nodes_by_path[path.parent]
            node: TreeNode[Path] = self._insert_node(
                dir_node=True, path=path, parent_node=parent_node
            )
            nodes_by_path[path] = node

        # Add all status file nodes
        for file_path in self.paths.status_files:
            parent_node = nodes_by_path[file_path.parent]
            self._insert_node(dir_node=False, path=file_path, parent_node=parent_node)

    def _insert_node(
        self, dir_node: bool, path: Path, parent_node: TreeNode[Path]
    ) -> TreeNode[Path]:

        # Avoid inserting an existing node twice or more.
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

            new_is_dir = dir_node

            # directories first, then files
            if child.allow_expand != new_is_dir:
                if new_is_dir:
                    before = index
                    break
            elif child.data.name.lower() > path.name.lower():
                before = index
                break

        node = parent_node.add(
            self._get_node_label(path, managed_kind, status_code),
            data=path,
            before=before,
            allow_expand=dir_node,
        )
        return node

    # #################################
    # # Watchers and message handling #
    # #################################

    @on(Tree.NodeCollapsed)
    def update_collapsed(self) -> None: ...

    @on(Tree.NodeExpanded)
    def update_expanded(self) -> None: ...

    @on(Tree.NodeSelected)
    def send_node_context_message(self, event: Tree.NodeSelected[Path]) -> None:
        if event.node.data is None:
            raise RuntimeError("Node data is None, which is unexpected.")
        is_unmanaged = (
            event.node.data not in self.paths.managed_dirs | self.paths.managed_files
            and event.node is not self.root
        )
        has_status = (
            event.node.data in self.paths.status_files
            or event.node.data in self.paths.status_dirs
        )
        is_ndir = event.node.data in self.paths.n_dirs
        self.post_message(
            CurrentNodeMsg(
                ids=self.app_ids,
                path=event.node.data,
                no_changed_paths=self.paths.no_status_paths,
                has_status=has_status,
                is_ndir=is_ndir,
                dest_dir=self.paths.dest_dir,
                is_unmanaged=is_unmanaged,
            )
        )

    def watch_show_unchanged(self, show_unchanged: bool) -> None:
        if show_unchanged:
            for path in self.paths.unchanged_tree_dirs:
                parent_node = self._get_tree_node(path, parent_node=True)
                if parent_node is not None:
                    self._insert_node(dir_node=True, path=path, parent_node=parent_node)

            for path in self.paths.unchanged_files:
                parent_node = self._get_tree_node(path, parent_node=True)
                if parent_node is not None:
                    self._insert_node(
                        dir_node=False, path=path, parent_node=parent_node
                    )

        else:
            for path in self.paths.unchanged_tree_dirs:
                node = self._get_tree_node(path, parent_node=False)
                if node is not None:
                    node.remove()
            for path in self.paths.unchanged_files:
                node = self._get_tree_node(path, parent_node=False)
                if node is not None:
                    node.remove()

    def watch_expand_all(self, expand_all: bool) -> None:
        if expand_all is True:
            self.root.expand_all()
        else:
            self.root.collapse_all()
            self.root.expand()  # keep root expanded

    def watch_show_unmanaged(self, show_unmanaged: bool) -> None:
        if show_unmanaged:
            expanded_dirs = [self.paths.dest_dir]
            expanded_dirs += [
                node.data
                for node in self._iter_tree_nodes()
                if node.allow_expand and node.is_expanded
            ]

            for dir_path in expanded_dirs:
                if dir_path is None:
                    raise RuntimeError("dir_path is None, which is unexpected.")
                unmanaged: ScanDirResult = CheckPath.os_scan_dir(
                    dir_path, managed_dir=True
                )
                if isinstance(unmanaged, PathKind):
                    continue  # TODO: handle this case
                for item in unmanaged:
                    if self.show_unchanged and (
                        item.path in self.paths.unchanged_tree_dirs
                        or item.path in self.paths.unchanged_files
                    ):
                        continue  # skip unchanged paths
                    parent_node = self._get_tree_node(item.path, parent_node=True)
                    if parent_node is not None:
                        self._insert_node(
                            dir_node=item.is_dir,
                            path=item.path,
                            parent_node=parent_node,
                        )
        else:
            # remove unmanaged nodes
            for node in self._iter_tree_nodes():
                if (
                    node.data not in self.paths.managed_dirs | self.paths.managed_files
                    and node is not self.root
                ):
                    node.remove()
