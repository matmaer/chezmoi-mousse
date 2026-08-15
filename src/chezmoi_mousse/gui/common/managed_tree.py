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
    current_dir_nodes: set[TreeNode[Path]] = field(default_factory=lambda: set())
    current_file_nodes: set[TreeNode[Path]] = field(default_factory=lambda: set())
    visible_dir_nodes: set[TreeNode[Path]] = field(default_factory=lambda: set())
    visible_file_nodes: set[TreeNode[Path]] = field(default_factory=lambda: set())
    show_unchanged: bool = False
    show_unmanaged: bool = False
    expand_all: bool = False


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
        self.root.allow_expand = False  # prevent from being collapsed when we select it
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
        self.state = ManagedTreeState(root_node=self.root, selected_node=self.root)

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

    def _get_tree_node(
        self, path: Path | None, *, parent_node: bool
    ) -> TreeNode[Path] | None:
        if path is None:
            return None
        for node in self._iter_tree_nodes():
            if parent_node:
                if node.data == path.parent:
                    return node
            else:
                if node.data == path:
                    return node
        return None

    def _get_node_children(self, node: TreeNode[Path]) -> list[TreeNode[Path]]:
        # get all children of a node, including the children of its children
        children: list[TreeNode[Path]] = []
        queue: deque[TreeNode[Path]] = deque([node])
        while queue:
            current_node = queue.popleft()
            children.append(current_node)
            queue.extend(current_node.children)
        return children

    def _best_effort_state_restore(self, old_state: ManagedTreeState) -> None:
        """After we do write operations, which may change the tree structure, we try to
        restore the previous state of the tree as best as we can.

        After write operations, or refresh tree requests, we call .update_tree() from
        other parts of the code. This will rebuild the tree structure, but we want to
        keep the previous state as best as we can.
        """
        # 1. We fold all non visible nodes, if they still exist
        for node in old_state.current_dir_nodes:
            if node.data in self.paths.tree_status_dirs:
                new_node = self._get_tree_node(node.data, parent_node=False)
                if new_node is not None:
                    if node.is_expanded:
                        new_node.expand()
                    else:
                        new_node.collapse()

        # 2. We try to reselect the previously selected node, if it still exists
        node = self._get_tree_node(old_state.selected_node.data, parent_node=False)
        if node is not None:
            self.select_node(node)
        else:
            self.select_node(self.root)

        # 3. We update the current state of the tree
        self._update_state()

    def _update_state(self) -> None:
        current_dir_nodes: set[TreeNode[Path]] = set()
        current_file_nodes: set[TreeNode[Path]] = set()
        for node in self._iter_tree_nodes():
            if node.data is not None:
                if node.allow_expand and node.is_expanded:
                    current_dir_nodes.add(node)
                else:
                    current_file_nodes.add(node)

        self.state.current_dir_nodes = current_dir_nodes
        self.state.current_file_nodes = current_file_nodes

    def update_tree(self) -> None:
        old_state = self.state

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

        # Try to restore the previous state of the tree
        self._best_effort_state_restore(old_state)

    def _insert_node(
        self, dir_node: bool, path: Path, parent_node: TreeNode[Path]
    ) -> TreeNode[Path]:
        def _get_node_label(
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
            _get_node_label(path, managed_kind, status_code),
            data=path,
            before=before,
            allow_expand=dir_node,
        )
        return node

    # #################################
    # # Watchers and message handling #
    # #################################

    @on(Tree.NodeCollapsed)
    def handle_node_collapsed(self, event: Tree.NodeCollapsed[Path]) -> None:
        if self.expand_all or self.show_unmanaged:
            return
        node_children = self._get_node_children(event.node)
        for child in node_children:
            if child in self.state.visible_dir_nodes:
                self.state.visible_dir_nodes.remove(child)
            if child in self.state.visible_file_nodes:
                self.state.visible_file_nodes.remove(child)

    @on(Tree.NodeExpanded)
    def handle_node_expanded(self, event: Tree.NodeExpanded[Path]) -> None:
        if self.expand_all or self.show_unmanaged:
            return
        for child in event.node.children:
            if child.allow_expand:
                self.state.visible_dir_nodes.add(child)
            else:
                self.state.visible_file_nodes.add(child)

    @on(Tree.NodeSelected)
    def send_node_context_message(self, event: Tree.NodeSelected[Path]) -> None:
        self.state.selected_node = event.node
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

    def watch_show_unchanged(self, show_unchanged: bool) -> None:
        self.state.show_unchanged = show_unchanged
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
        self.state.expand_all = expand_all
        if expand_all is True:
            self.root.expand_all()
        else:
            # we return to the previous state
            for node in self.state.visible_dir_nodes:
                if not node.is_expanded:
                    node.expand()
                else:
                    node.collapse()

    def watch_show_unmanaged(self, show_unmanaged: bool) -> None:
        self.state.show_unmanaged = show_unmanaged
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
