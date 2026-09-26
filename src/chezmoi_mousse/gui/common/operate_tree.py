from __future__ import annotations

from typing import TYPE_CHECKING

from textual import on, work
from textual.widgets import Tree

from chezmoi_mousse import path_funcs, store
from chezmoi_mousse.named_tuples import NodeData
from chezmoi_mousse.str_enums import (
    ColorVar,
    StatusCode as Sc,
    Tcss,
    TreeName,
)

if TYPE_CHECKING:
    from pathlib import Path

    from textual import getters
    from textual.widgets.tree import TreeNode

    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.named_tuples import IterDirResult


__all__ = ["OperateTree"]


class OperateTree(Tree[NodeData]):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(self, tree_name: TreeName, tree_id: str) -> None:
        super().__init__(
            id=tree_id,
            label="root",
            name=tree_name.value,
            classes=Tcss.managed_tree,
        )

    def on_mount(self) -> None:
        self.dir_node_map: dict[Path, TreeNode[NodeData]] = {}
        self.scanned_dirs: set[Path] = set()
        self.loading = True
        self.display = False
        self.guide_depth = 3
        self.show_root = False
        self.initial_tree_population()

    def _get_tree_nodes(
        self, node_data_dict: dict[Path, NodeData]
    ) -> dict[Path, NodeData]:
        result: dict[Path, NodeData] | None = None
        if self.name in (TreeName.managed_only_sp, TreeName.managed_only_sp_xpd):
            result = {
                path: node_data
                for path, node_data in node_data_dict.items()
                if node_data.status not in (Sc.XX, Sc.UU, Sc.SS)
            }
        elif self.name in (TreeName.managed_all_mp, TreeName.managed_all_mp_xpd):
            result = {
                path: node_data
                for path, node_data in node_data_dict.items()
                if node_data.status not in (Sc.XX, Sc.UU)
            }
        elif self.name in (
            TreeName.un_man_plus_sp,
            TreeName.un_man_plus_sp_xpd,
        ):
            result = {
                path: node_data
                for path, node_data in node_data_dict.items()
                if node_data.status not in (Sc.XX, Sc.SS)
            }
        elif self.name in (
            TreeName.un_man_plus_amp,
            TreeName.un_man_plus_amp_xpd,
        ):
            result = {
                path: node_data
                for path, node_data in node_data_dict.items()
                if node_data.status != Sc.XX
            }
        elif self.name in (
            TreeName.un_wanted_plus_sp,
            TreeName.un_wanted_plus_sp_xpd,
        ):
            result = {
                path: node_data
                for path, node_data in node_data_dict.items()
                if node_data.status != Sc.SS
            }
        elif self.name in (
            TreeName.un_wanted_plus_amp,
            TreeName.un_wanted_plus_amp_xpd,
        ):
            result = dict(node_data_dict.items())
        else:
            raise ValueError(f"Unknown tree name: {self.name}")
        return path_funcs.sort_path_dict(result)

    def _color_label(self, path: Path, status: Sc, directory: bool) -> str:
        color_var = status.dir_color if directory else status.file_color
        italic = " italic" if path in store.cm_paths.missing_managed else ""
        color = self.app.theme_variables.get(color_var, ColorVar.bogus.value)
        return f"[{color}{italic}]{path.name}[/]"

    async def _add_node_with_color(
        self, path: Path, node_data: NodeData, *, allow_expand: bool
    ) -> None:
        if path.parent == store.cfg.dest_dir:
            parent_node = self.root
        else:
            parent_node = self.dir_node_map[path.parent]
        label = self._color_label(path, node_data.status, allow_expand)
        new_node = parent_node.add(
            label=label,
            data=node_data,
            allow_expand=allow_expand,
        )
        if allow_expand:
            self.dir_node_map[path] = new_node

    def expand_xpd_nodes(self) -> None:
        if self.name in (
            TreeName.managed_only_sp_xpd,
            TreeName.managed_all_mp_xpd,
        ):
            self.root.expand_all()
        elif self.name in (
            TreeName.un_man_plus_sp_xpd,
            TreeName.un_man_plus_amp_xpd,
            TreeName.un_wanted_plus_sp_xpd,
            TreeName.un_wanted_plus_amp_xpd,
        ):
            for path, node in self.dir_node_map.items():
                if path in store.cm_paths.man_dir_set:
                    node.expand()

    @work
    async def initial_tree_population(self) -> None:
        dir_nodes = self._get_tree_nodes(store.cm_paths.dir_node_data)
        file_nodes = self._get_tree_nodes(store.cm_paths.file_node_data)
        for path, node_data in dir_nodes.items():
            await self._add_node_with_color(path, node_data, allow_expand=True)
        for path, node_data in file_nodes.items():
            await self._add_node_with_color(path, node_data, allow_expand=False)
        self.expand_xpd_nodes()
        if self.name == TreeName.managed_only_sp:
            self.select_node(self.root)
            self.unselect()  # otherwise it looks like the first node is selected
            self.display = True
        self.loading = False

    @work
    async def add_unmanaged_dir_children(self, node_data: NodeData) -> None:
        scan_dir_result: IterDirResult = path_funcs.get_unmanaged_children(
            node_data.path
        )
        self.scanned_dirs.add(node_data.path)
        for path, status in scan_dir_result.dirs.items():
            await self._add_node_with_color(path, status, allow_expand=True)
        for path, status in scan_dir_result.files.items():
            await self._add_node_with_color(path, status, allow_expand=False)

    @on(Tree.NodeExpanded)
    def populate_unmanaged_dir(self, event: Tree.NodeExpanded[NodeData]) -> None:
        # dest dir node data is none
        if event.node.data is None:
            return
        if (
            # immediately skip for managed trees
            self.name
            in (
                TreeName.managed_only_sp,
                TreeName.managed_only_sp_xpd,
                TreeName.managed_all_mp,
                TreeName.managed_all_mp_xpd,
            )
            # for path.parent below, we have it from the 'chezmoi unmanaged' output
            or event.node.data.path.parent
            in (store.cm_paths.man_dir_set, store.cfg.dest_dir)
            # skip if the directory has already been scanned
            or event.node.data.path in self.scanned_dirs
        ):
            return
        self.add_unmanaged_dir_children(event.node.data)
