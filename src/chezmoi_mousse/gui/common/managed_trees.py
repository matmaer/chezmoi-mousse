from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.widgets import (
    Tree,
)

from chezmoi_mousse import store
from chezmoi_mousse.data_classes import ChezmoiPaths
from chezmoi_mousse.gui.common.messages import TreeStateMsg
from chezmoi_mousse.str_enums import (
    ColorVar,
    Tcss,
    TreeName,
)

if TYPE_CHECKING:
    from textual import getters
    from textual.widgets.tree import TreeNode

    from chezmoi_mousse.gui.textual_app import ChezmoiGui


type NodeMap = dict[Path, TreeNode[Path]]


__all__ = ["ChezmoiTree", "ManagedTree", "StatusTree"]


class _ManagedTreeBase(Tree[Path]):
    """Base class for the managed tree with unchanged paths, without unchanged paths,
    and with unmanaged or unwanted paths."""

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(self, tree_name: TreeName) -> None:
        self.node_color_map: dict[Path, str] = {}
        self.node_map: NodeMap = {}
        self.cm_paths = ChezmoiPaths.empty()
        super().__init__(label="root", classes=Tcss.managed_tree, name=tree_name)

    def on_mount(self) -> None:
        self.root.data = store.cfg.dest_dir_path
        self.guide_depth = 3
        self.show_root = False

    def color_label(self, path: Path, cm_paths: ChezmoiPaths) -> str:
        if self.node_color_map.get(path, None) is not None:
            return f"[{self.node_color_map[path]}]{path.name}[/]"
        color_var = ColorVar.bogus
        if path in cm_paths.managed_dirs:
            if path in cm_paths.sets.dirty_space_dirs:
                color_var = ColorVar.text_primary
            else:
                status = cm_paths.managed_dirs[path]
                color_var = ColorVar.dimmed if status == "  " else ColorVar.text_warning
        elif path in cm_paths.managed_files:
            status = cm_paths.managed_files[path]
            color_var = ColorVar.dimmed if status == "  " else ColorVar.text_warning
        italic = " italic" if path in cm_paths.sets.missing_paths else ""
        color = self.app.theme_variables.get(color_var.value, ColorVar.bogus.value)
        self.node_color_map[path] = color
        return f"[{color}{italic}]{path.name}[/]"

    def add_node(self, path: Path, allow_expand: bool) -> None:
        parent_node = self.node_map.get(path.parent, self.root)
        label = self.color_label(path, self.cm_paths)
        new_node = parent_node.add(label=label, data=path, allow_expand=allow_expand)
        self.node_map[path] = new_node

    def should_include_dir(self, _path: Path, _status: str) -> bool:
        return True

    def should_include_file(self, _path: Path, _status: str) -> bool:
        return True

    async def update_tree(self, cm_paths: ChezmoiPaths) -> None:
        self.cm_paths = cm_paths

        for path, status in cm_paths.chezmoi_dirs.items():
            if self.should_include_dir(path, status):
                self.add_node(path, allow_expand=True)

        for path, status in cm_paths.chezmoi_files.items():
            if self.should_include_file(path, status):
                self.add_node(path, allow_expand=False)

    @on(Tree.NodeCollapsed)
    def handle_node_collapsed(self, event: Tree.NodeCollapsed[Path]) -> None:
        self.call_next(self.send_tree_state_message, event.node.data)

    @on(Tree.NodeExpanded)
    def handle_node_expanded(self, event: Tree.NodeExpanded[Path]) -> None:
        self.call_next(self.send_tree_state_message, event.node.data)

    @on(Tree.NodeSelected)
    def send_node_context_message(self, event: Tree.NodeSelected[Path]) -> None:
        self.call_next(self.send_tree_state_message, event.node.data)

    def send_tree_state_message(self, path: Path) -> None:
        assert self.name is not None
        self.app.post_message(TreeStateMsg(path, self.name, self.node_map))


class ManagedTree(_ManagedTreeBase):
    def __init__(self) -> None:
        super().__init__(tree_name=TreeName.managed_tree)

    def on_mount(self) -> None:
        super().on_mount()
        self.display = False

    def should_include_dir(self, path: Path, status: str) -> bool:
        return path not in self.cm_paths.sets.clean_space_dirs and status != "xx"

    def should_include_file(self, _: Path, status: str) -> bool:
        return status != "xx"


class StatusTree(_ManagedTreeBase):
    def __init__(self) -> None:
        super().__init__(tree_name=TreeName.status_tree)

    def on_mount(self) -> None:
        super().on_mount()
        self.display = True

    def should_include_dir(self, path: Path, status: str) -> bool:
        return path in self.cm_paths.sets.clean_space_dirs and status != "xx"

    def should_include_file(self, _: Path, status: str) -> bool:
        return status != "  " and status != "xx"


class ChezmoiTree(_ManagedTreeBase):
    def __init__(self) -> None:
        super().__init__(tree_name=TreeName.chezmoi_tree)

    def on_mount(self) -> None:
        super().on_mount()
        self.display = False
