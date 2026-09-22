from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual import work
from textual.widgets import Tree

from chezmoi_mousse import store
from chezmoi_mousse.str_enums import (
    ColorVar,
    Tcss,
)

if TYPE_CHECKING:
    from textual import getters
    from textual.widgets.tree import TreeNode

    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.str_enums import StatusCode as Sc


type NodeMap = dict[Path, TreeNode[Path]]


__all__ = [
    "NodeMap",
    "OperateTree",
]


class OperateTree(Tree[Path]):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(
        self, tree_id: str, dirs: dict[Path, Sc], files: dict[Path, Sc]
    ) -> None:
        self.node_map: NodeMap = {}
        self.dir_nodes: dict[Path, Sc] = dirs
        self.file_nodes: dict[Path, Sc] = files
        super().__init__(
            id=tree_id,
            label="root",
            classes=Tcss.managed_tree,
        )

    def on_mount(self) -> None:
        self.loading = True
        self.display = False
        self.root.data = store.cfg.dest_dir
        self.guide_depth = 3
        self.show_root = False
        self.initial_tree_population(self.dir_nodes, self.file_nodes)

    def color_label(self, path: Path, status: Sc, directory: bool) -> str:
        color_var = status.dir_color if directory else status.file_color
        italic = " italic" if path in store.cm_paths.missing_managed else ""
        color = self.app.theme_variables.get(color_var, ColorVar.bogus.value)
        return f"[{color}{italic}]{path.name}[/]"

    def add_node(self, path: Path, status: Sc, *, allow_expand: bool) -> None:
        parent_node = self.node_map.get(path.parent, self.root)
        label = self.color_label(path, status, allow_expand)
        new_node = parent_node.add(label=label, data=path, allow_expand=allow_expand)
        self.node_map[path] = new_node

    @work
    async def populate_tree(self, dirs: dict[Path, Sc], files: dict[Path, Sc]) -> None:
        for path, status in dirs.items():
            self.add_node(path, status, allow_expand=True)
        for path, status in files.items():
            self.add_node(path, status, allow_expand=False)

    @work
    async def initial_tree_population(
        self, dirs: dict[Path, Sc], files: dict[Path, Sc]
    ) -> None:
        for path, status in dirs.items():
            self.add_node(path, status, allow_expand=True)
        for path, status in files.items():
            self.add_node(path, status, allow_expand=False)
        if self.id in (
            store.op_ids.tree.status_xpd,
            store.op_ids.tree.managed_xpd,
            store.op_ids.tree.un_managed_xpd,
            store.op_ids.tree.un_wanted_xpd,
        ):
            self.root.expand_all()
        self.select_node(self.root)
        self.unselect()  # otherwise it looks like the first node is selected
        if self.id == store.op_ids.tree.status:
            self.display = True
        self.loading = False
