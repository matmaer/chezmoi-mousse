from __future__ import annotations

from typing import TYPE_CHECKING

from textual import on, work
from textual.widgets import Tree

from chezmoi_mousse import path_funcs, store
from chezmoi_mousse.data_types import NodeData
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

    from chezmoi_mousse.data_types import IterDirResult
    from chezmoi_mousse.gui.textual_app import ChezmoiGui


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
        self.iterated_dirs: set[Path] = set()
        self.loading = True
        self.display = False
        self.guide_depth = 3
        self.show_root = False
        self.root.data = store.cm_paths.dest_dir_node_data
        self.node_map: dict[Path, TreeNode[NodeData]] = {store.cfg.dest_dir: self.root}
        self._initial_tree_population()

    def _get_tree_nodes(
        self, node_data_dict: dict[Path, NodeData]
    ) -> dict[Path, NodeData]:
        result: dict[Path, NodeData] | None = None
        if self.name in (TreeName.managed_only_sp, TreeName.managed_only_sp_xpd):
            result = {
                path: node_data
                for path, node_data in node_data_dict.items()
                if node_data.status_dir
                or node_data.status_file
                or node_data.has_nested_status
            }
        elif self.name in (
            TreeName.managed_all_mp,
            TreeName.managed_all_mp_xpd,
        ):
            result = {
                path: node_data
                for path, node_data in node_data_dict.items()
                if not (node_data.un_man_dir or node_data.un_man_file)
                or (
                    node_data.status_dir
                    or node_data.status_file
                    or node_data.has_nested_status
                )
            }

        elif self.name in (
            TreeName.un_man_plus_sp,
            TreeName.un_man_plus_sp_xpd,
        ):
            result = {
                path: node_data
                for path, node_data in node_data_dict.items()
                if not node_data.un_wanted_file
                or not node_data.un_wanted_dir
                or node_data.status_dir
                or node_data.status_file
                or node_data.un_man_dir
                or node_data.un_man_file
            }
        elif self.name in (
            TreeName.un_man_plus_amp,
            TreeName.un_man_plus_amp_xpd,
        ):
            result = {
                path: node_data
                for path, node_data in node_data_dict.items()
                if not node_data.un_wanted_file
                or not node_data.un_wanted_dir
                or node_data.managed_dir
                or node_data.managed_file
                or node_data.un_man_dir
                or node_data.un_man_file
            }
        elif self.name in (
            TreeName.un_wanted_plus_sp,
            TreeName.un_wanted_plus_sp_xpd,
        ):
            result = {
                path: node_data
                for path, node_data in node_data_dict.items()
                if not node_data.un_wanted_file
                or not node_data.un_wanted_dir
                or node_data.status_dir
                or node_data.status_file
                or node_data.un_man_dir
                or node_data.un_man_file
            }
        elif self.name in (
            TreeName.un_wanted_plus_amp,
            TreeName.un_wanted_plus_amp_xpd,
        ):
            result = {
                path: node_data
                for path, node_data in node_data_dict.items()
                if not node_data.un_wanted_file
                or not node_data.un_wanted_dir
                or node_data.managed_dir
                or node_data.managed_file
                or node_data.un_man_dir
                or node_data.un_man_file
            }
        else:
            raise ValueError(f"Unknown tree name: {self.name}")
        return path_funcs.sort_path_dict(result)

    def _tree_label_color(self, node_data: NodeData) -> ColorVar:
        status_code = node_data.status
        mapping: dict[str | None, ColorVar] = {
            # D combos
            Sc.DA: ColorVar.text_warning,
            Sc.DD: ColorVar.text_warning,  # probably impossible status pair
            Sc.DM: ColorVar.text_warning,
            Sc.DS: ColorVar.text_warning,
            # M combos
            Sc.MA: ColorVar.text_warning,
            Sc.MD: ColorVar.text_warning,
            Sc.MM: ColorVar.text_warning,
            Sc.MS: ColorVar.text_warning,
            # S combos
            Sc.SA: ColorVar.text_warning,
            Sc.SD: ColorVar.text_warning,
            Sc.SM: ColorVar.text_warning,
            # Meta codes
            # "un-managed": ColorVar.text_success,
            # Meta code for space dirs containing nested status paths
            # Sc.VV: ColorVar.foreground_darken_3,
            # Sc.YY: ColorVar.text_success,
            # Sc.ZZ: ColorVar.text_accent,
        }
        color_var: ColorVar = mapping.get(status_code, ColorVar.error_muted)
        if color_var is not ColorVar.error_muted:
            if node_data.status_dir:
                color_var = ColorVar.warning_lighten_3
            return color_var

        if node_data.has_nested_status:
            color_var = ColorVar.text_primary
        elif (
            node_data.has_nested_managed_dirs
            and self.name not in TreeName.managed_trees()
        ):
            color_var = ColorVar.text
        elif status_code is ColorVar.error_muted:
            if node_data.known_dir:
                status_code = ColorVar.foreground_darken_2
            else:
                status_code = ColorVar.foreground_darken_3

        return color_var

    async def _add_node_with_color(
        self, path: Path, node_data: NodeData, *, allow_expand: bool
    ) -> None:
        if path == store.cfg.dest_dir:
            return
        parent_node = self.node_map[path.parent]

        italic = " italic" if not node_data.exists else ""
        color = self.app.theme_variables[self._tree_label_color(node_data)]

        new_node = parent_node.add(
            label=f"[{color}{italic}]{path.name}[/]",
            data=node_data,
            allow_expand=allow_expand,
        )
        self.node_map[path] = new_node

    def _expand_xpd_nodes(self) -> None:
        if self.name in (
            TreeName.managed_only_sp_xpd,
            TreeName.managed_all_mp_xpd,
            TreeName.un_man_plus_sp_xpd,
            TreeName.un_man_plus_amp_xpd,
            TreeName.un_wanted_plus_sp_xpd,
            TreeName.un_wanted_plus_amp_xpd,
        ):
            for node in self.node_map.values():
                if node.data is not None and node.data.managed_dir:
                    node.expand()

    @work
    async def _initial_tree_population(self) -> None:
        dir_nodes = self._get_tree_nodes(store.cm_paths.dir_node_data)
        file_nodes = self._get_tree_nodes(store.cm_paths.file_node_data)

        # add missing parent directories for trees that could have missing parents
        for path in (*dir_nodes, *file_nodes):
            parent_path = path.parent
            while (
                parent_path != store.cfg.dest_dir
                and parent_path not in store.cfg.dest_dir.parents
            ):
                if parent_path not in dir_nodes:
                    dir_nodes[parent_path] = store.cm_paths.dir_node_data[parent_path]
                parent_path = parent_path.parent

        dir_nodes = path_funcs.sort_path_dict(dir_nodes)
        file_nodes = path_funcs.sort_path_dict(file_nodes)

        for path, node_data in dir_nodes.items():
            await self._add_node_with_color(path, node_data, allow_expand=True)
        for path, node_data in file_nodes.items():
            await self._add_node_with_color(path, node_data, allow_expand=False)
        self._expand_xpd_nodes()
        self.select_node(self.root)
        self.unselect()  # otherwise it looks like the first node is selected
        if self.name == TreeName.managed_only_sp:
            self.display = True
        self.loading = False

    @work
    async def _add_unmanaged_dir_children(self, dir_node_data: NodeData) -> None:
        iter_dir_result: IterDirResult = path_funcs.get_un_man_children(
            dir_node_data.path
        )
        self.iterated_dirs.add(dir_node_data.path)
        for path, node_data in iter_dir_result.dirs.items():
            await self._add_node_with_color(path, node_data, allow_expand=True)
        for path, node_data in iter_dir_result.files.items():
            await self._add_node_with_color(path, node_data, allow_expand=False)

    @on(Tree.NodeExpanded)
    def populate_unmanaged_dir(self, event: Tree.NodeExpanded[NodeData]) -> None:
        # dest dir node data is none
        if (
            event.node.data is None
            or event.node.data.managed_dir
            or event.node.data.path in self.iterated_dirs
        ):
            return
        self._add_unmanaged_dir_children(event.node.data)
