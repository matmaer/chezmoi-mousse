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

from chezmoi_mousse.enum_data import OpBtnEnum
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
    from chezmoi_mousse.cm_types import TreeNodeDict
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

from .actionables import OpButton
from .messages import CurrentNodeMsg

__all__ = ["ManagedTree", "DestDirTree"]


class DestDirTree(Vertical):

    def __init__(self, ids: AppIds) -> None:
        self.app_ids = ids
        super().__init__(id=ids.container.left_side, classes=Tcss.tab_left_vertical)

    def compose(self) -> ComposeResult:
        yield Label("destDir tree", classes=Tcss.dest_dir_tree_label)
        yield ManagedTree(self.app_ids)
        yield OpButton(
            btn_enum=OpBtnEnum.refresh_tree,
            btn_id=self.app_ids.op_btn.refresh_tree,
            app_ids=self.app_ids,
        )


@dataclass(slots=True, frozen=True)
class ManagedTreeState:
    root_node: TreeNode[Path]
    all_dir_nodes: TreeNodeDict
    all_file_nodes: TreeNodeDict
    selected_node: TreeNode[Path] | None
    show_unchanged: bool
    show_unmanaged: bool
    expand_all: bool

    @property
    def expanded_dir_nodes(self) -> TreeNodeDict:
        return {
            p: n
            for p, n in self.all_dir_nodes.items()
            if n.parent is not None and n.parent.is_expanded
        }

    @property
    def visible_dir_nodes(self) -> TreeNodeDict:
        return {
            p: n
            for p, n in self.expanded_dir_nodes.items()
            if n.parent is not None
            and n.parent.is_expanded
            or n.parent is self.root_node
        }

    @property
    def visible_file_nodes(self) -> TreeNodeDict:
        return {
            p: n
            for p, n in self.all_file_nodes.items()
            if n.parent is not None and n.parent in self.visible_dir_nodes.values()
        }


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
        self.root.allow_expand = False  # prevent from being collapsed

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

    def _snapshot_tree_state(self) -> ManagedTreeState:
        current_dir_nodes: TreeNodeDict = {}
        current_file_nodes: TreeNodeDict = {}
        for node in self._iter_tree_nodes():
            if node.data is not None:
                if node.allow_expand:
                    current_dir_nodes[node.data] = node
                else:
                    current_file_nodes[node.data] = node
        return ManagedTreeState(
            root_node=self.root,
            all_dir_nodes=current_dir_nodes,
            all_file_nodes=current_file_nodes,
            selected_node=self.cursor_node,
            show_unchanged=self.show_unchanged,
            show_unmanaged=self.show_unmanaged,
            expand_all=self.expand_all,
        )

    def _add_unchanged_nodes(self) -> None:
        """First add unchanged directories, then add unchanged files.

        This ensures that all parent directories are present before adding files.
        """
        ...

    def _remove_unchanged_nodes(self) -> None:
        """Removes unchanged nodes from the tree, first the files, then the directories
        if they no longer contain any files."""
        ...

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
            color = self.app.get_color(status_code)
        else:
            color = self.app.get_color(StatusCode.Space)
        # determine if the label should be italic or not
        italic = ""
        if managed_kind == PathKind.EXISTS_FALSE:
            italic = " italic"
        return f"[{color}{italic}]{node_path.name}[/]"

    def populate_tree(self) -> None:
        current_state = self._snapshot_tree_state()
        for dir_path in self.paths.tree_status_dirs:
            parent_path = dir_path.parent
            parent_node = current_state.all_dir_nodes.get(parent_path, self.root)
            self._insert_dir_node(parent_node, dir_path)
        for file_path in self.paths.status_files:
            parent_path = file_path.parent
            parent_node = current_state.all_dir_nodes.get(parent_path, self.root)
            self._insert_file_node(
                parent_node, file_path
            )  # update state after adding files

    def _insert_dir_node(self, parent_node: TreeNode[Path], dir_path: Path) -> None:
        """Inserts a child directory node for a given parent alphabetically."""
        # determine before_node value
        dir_children = (c for c in parent_node.children if c.allow_expand)
        before_node = next(
            (
                n
                for n in dir_children
                if n.data is not None and n.data.name.lower() > dir_path.name.lower()
            ),
            None,
        )
        # look up the dir_path in self.paths.managed_dirs to get the PathKind
        managed_kind = self.paths.managed_dirs.get(dir_path, None)
        # look up the dir_path in self.paths.tree_status_dirs to get the StatusCode
        status_code = self.paths.tree_status_dirs.get(dir_path, None)

        # call _insert_node
        self._insert_node(
            allow_expand=True,
            before_node=before_node,
            data=dir_path,
            label=self._get_node_label(dir_path, managed_kind, status_code),
            parent_node=parent_node,
        )

    def _insert_file_node(self, parent_node: TreeNode[Path], file_path: Path) -> None:
        """Inserts a file node for a given parent alphabetically."""
        file_children = (c for c in parent_node.children if not c.allow_expand)
        before_node = next(
            (
                n
                for n in file_children
                if n.data is not None and n.data.name.lower() > file_path.name.lower()
            ),
            None,
        )
        # look up the file_path in self.paths.managed_files to get the PathKind
        managed_kind = self.paths.managed_files.get(file_path, None)
        # look up the file_path in self.paths.status_files to get the StatusCode
        status_code = self.paths.status_files.get(file_path, None)

        # call _insert_node
        self._insert_node(
            allow_expand=False,
            before_node=before_node,
            data=file_path,
            label=self._get_node_label(file_path, managed_kind, status_code),
            parent_node=parent_node,
        )

    def _insert_node(
        self,
        allow_expand: bool,
        before_node: TreeNode[Path] | None,
        data: Path,
        label: str,
        parent_node: TreeNode[Path],
    ) -> None:
        state = self._snapshot_tree_state()
        if data in state.all_dir_nodes or data in state.all_file_nodes:
            return  # node already exists, do not insert again
        parent_node.add(label, data=data, before=before_node, allow_expand=allow_expand)

    # #################################
    # # Watchers and message handling #
    # #################################

    @on(Tree.NodeCollapsed)
    def update_collapsed(self) -> None: ...

    @on(Tree.NodeExpanded)
    def update_expanded(self) -> None: ...

    @on(Tree.NodeSelected)
    def send_node_context_message(self, event: Tree.NodeSelected[Path]) -> None:
        if event.node.data is not None:
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
                )
            )

    def watch_show_unchanged(self, show_unchanged: bool) -> None:
        if show_unchanged:
            self._add_unchanged_nodes()
        else:
            self._remove_unchanged_nodes()

    def watch_expand_all(self, expand_all: bool) -> None:
        if expand_all is True:
            self.root.expand_all()
        else:
            self.root.collapse_all()

    def watch_show_unmanaged(self) -> None:
        self.notify("Not implemented yet: show_unmanaged watcher")
