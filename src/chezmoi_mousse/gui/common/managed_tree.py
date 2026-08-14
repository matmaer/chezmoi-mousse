from __future__ import annotations

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
from chezmoi_mousse.named_tuples import ManagedTreePaths
from chezmoi_mousse.str_enums import Chars, PathKind, StatusCode, TabLabel, Tcss

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
    all_dir_nodes: TreeNodeDict = field(default_factory=lambda: {})
    all_file_nodes: TreeNodeDict = field(default_factory=lambda: {})

    @property
    def visible_dir_nodes(self) -> TreeNodeDict:
        return {
            p: n
            for p, n in self.all_dir_nodes.items()
            if n.parent is not None and n.parent.is_expanded
        }

    @property
    def visible_expanded_dir_nodes(self) -> TreeNodeDict:
        return {p: n for p, n in self.visible_dir_nodes.items() if n.is_expanded}

    @property
    def visible_file_nodes(self) -> TreeNodeDict:
        return {
            p: n
            for p, n in self.all_file_nodes.items()
            if n.parent is not None and n.parent.is_expanded
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
        self.first_time_populating = False

        # configure root node
        self.root.data = self.app.cmattr.dest_dir
        color = self.app.theme_variables["text-primary"]
        self.root.label = f"[{color} bold]{self.app.cmattr.dest_dir.name}[/]"
        self.root.expand()
        self.root.allow_expand = False  # prevent from being collapsed
        # keep state
        self.state = ManagedTreeState()

    @property
    def paths(self) -> ManagedTreePaths:
        return (
            self.app.cmattr.paths.apply_tree_paths
            if self.app_ids.tab_label == TabLabel.apply
            else self.app.cmattr.paths.re_add_tree_paths
        )

    def _create_colored_label(self, path: Path) -> str:
        if path in self.paths.n_dirs:
            color = self.app.get_color(PathKind.N_DIR)
        elif path in self.paths.status_dirs_map:
            color = self.app.get_color(self.paths.status_dirs_map[path])
        elif path in self.paths.status_files_map:
            color = self.app.get_color(self.paths.status_files_map[path])
        elif path in self.paths.unchanged_dirs or path in self.paths.unchanged_files:
            color = self.app.get_color(StatusCode.Space)
        elif (
            path not in self.paths.managed_dirs_map
            and path not in self.paths.managed_files_map
        ):
            color = self.app.get_color(PathKind.UNMANAGED)
        else:
            color = self.app.get_color(None)
        italic = " italic" if not path.exists() else ""
        return f"[{color}{italic}]{path.name}[/]"

    def _get_nodes_bfs(self, path_kind: PathKind) -> TreeNodeDict:
        # BFS approach using deque for O(1) pops from the left.

        queue = deque([self.root])  # add the root node as it's not allowed to expand
        if path_kind == PathKind.dir:
            queue.extend(deque(n for n in self.root.children if n.allow_expand))
        elif path_kind == PathKind.file:
            queue.extend(deque(n for n in self.root.children if not n.allow_expand))

        nodes_dict: dict[Path, TreeNode[Path]] = {}

        while queue:
            node = queue.popleft()
            if node.data is None:
                raise RuntimeError(f"{node.label}: Path is None.")
            nodes_dict[node.data] = node
            queue.extend(node.children)

        return nodes_dict

    def _update_tree_state(self) -> None:
        all_dir_nodes = self._get_nodes_bfs(PathKind.dir)
        all_file_nodes = self._get_nodes_bfs(PathKind.file)
        self.state = ManagedTreeState(
            all_dir_nodes=all_dir_nodes, all_file_nodes=all_file_nodes
        )

    def populate_tree(self) -> None:
        self.root.remove_children()

        dir_queue: deque[TreeNode[Path]] = deque([self.root])
        remaining_dirs = set(self.paths.tree_status_dirs)

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
                child_node = self._insert_node(parent_node=parent_node, path=child_dir)
                dir_queue.append(child_node)
                remaining_dirs.remove(child_dir)

        current_dir_nodes = self._get_nodes_bfs(path_kind=PathKind.dir)

        for path in self.paths.status_files_map:
            parent_node = current_dir_nodes[path.parent]
            self._insert_node(parent_node, path)

        # expand all switch is false by default, tree state does not matter yet
        if self.first_time_populating:
            self.first_time_populating = False
            self.root.collapse_all()
            self.root.expand()
            self.select_node(self.root)
            return

    def _insert_node(self, parent_node: TreeNode[Path], path: Path) -> TreeNode[Path]:
        """Inserts a dir node or file node alphabetically, using is_file to determine
        where as we keep children which are directories on top followed by the children
        which are files."""
        is_dir_path = path in self.paths.managed_dirs_map or path.is_dir()
        children = parent_node.children
        path_label = self._create_colored_label(path)

        if not children:
            return parent_node.add(path_label, data=path, allow_expand=is_dir_path)
        elif is_dir_path:
            node_context = [c for c in children if c.allow_expand]
        else:
            node_context = [c for c in children if not c.allow_expand]

        before_node = next(
            (
                n
                for n in node_context
                if n.data is not None and n.data.name.lower() > path.name.lower()
            ),
            None,
        )
        return parent_node.add(
            path_label, data=path, before=before_node, allow_expand=is_dir_path
        )

    # #################################
    # # Watchers and message handling #
    # #################################

    @on(Tree.NodeCollapsed)
    def update_collapsed(self) -> None: ...

    @on(Tree.NodeExpanded)
    def update_expanded(self) -> None:
        if not self.expand_all:
            ...

    @on(Tree.NodeSelected)
    def send_node_context_message(self, event: Tree.NodeSelected[Path]) -> None:
        if event.node.data is not None:
            has_status = (
                event.node.data in self.paths.status_files_map
                or event.node.data in self.paths.status_dirs_map
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
            for path in self.paths.unchanged_dirs | self.paths.unchanged_files:
                parent_node: TreeNode[Path] | None = (
                    self.state.visible_expanded_dir_nodes.get(path.parent)
                )
                if parent_node is None and path.parent == self.root.data:
                    parent_node = self.root
                if parent_node is not None:
                    self._insert_node(parent_node, path)
        else:
            ...
        self._update_tree_state()

    def watch_expand_all(self, expand_all: bool) -> None:
        if expand_all is True:
            self.root.expand_all()
