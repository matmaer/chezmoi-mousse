from __future__ import annotations

from typing import TYPE_CHECKING

from textual import on, work
from textual.widgets import Tree

from chezmoi_mousse import path_funcs, store
from chezmoi_mousse.named_tuples import NodeData
from chezmoi_mousse.str_enums import (
    LabelStr,
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
        self.iterated_dirs: set[Path] = set()
        self.loading = True
        self.display = False
        self.guide_depth = 3
        self.show_root = False
        self.root.data = NodeData(
            path=store.cfg.dest_dir, status=Sc.QQ, main_label=LabelStr.dest_dir
        )
        self.node_map: dict[Path, TreeNode[NodeData]] = {store.cfg.dest_dir: self.root}
        self._initial_tree_population()

    def _get_tree_nodes(
        self, node_data_dict: dict[Path, NodeData]
    ) -> dict[Path, NodeData]:
        result: dict[Path, NodeData] | None = None
        if self.name == TreeName.managed_only_sp:
            result = {
                path: node_data
                for path, node_data in node_data_dict.items()
                if node_data.status not in (Sc.XX, Sc.UU, Sc.SS, Sc.YY, Sc.ZZ)
            }
        elif self.name == TreeName.managed_all_mp:
            result = {
                path: node_data
                for path, node_data in node_data_dict.items()
                if node_data.status not in (Sc.XX, Sc.UU)
            }
        elif self.name == TreeName.un_man_plus_sp:
            result = {
                path: node_data
                for path, node_data in node_data_dict.items()
                if node_data.status not in (Sc.XX, Sc.SS, Sc.ZZ)
            }
        elif self.name == TreeName.un_man_plus_amp:
            result = {
                path: node_data
                for path, node_data in node_data_dict.items()
                if node_data.status != Sc.XX
            }
        elif self.name == TreeName.un_wanted_plus_sp:
            result = {
                path: node_data
                for path, node_data in node_data_dict.items()
                if node_data.status != Sc.SS
            }
        elif self.name == TreeName.un_wanted_plus_amp:
            result = dict(node_data_dict.items())
        else:
            raise ValueError(f"Unknown tree name: {self.name}")
        return path_funcs.sort_path_dict(result)

    async def _add_node_with_color(
        self, path: Path, node_data: NodeData, *, allow_expand: bool
    ) -> None:
        parent_node = self.node_map[path.parent]

        italic = " italic" if path in store.cm_paths.missing_managed else ""
        color = self.app.theme_variables[node_data.status.tree_label_color]

        new_node = parent_node.add(
            label=f"[{color}{italic}]{path.name}[/]",
            data=node_data,
            allow_expand=allow_expand,
        )
        self.node_map[path] = new_node

    @work
    async def _initial_tree_population(self) -> None:
        dir_nodes = self._get_tree_nodes(store.cm_paths.dir_node_data)
        file_nodes = self._get_tree_nodes(store.cm_paths.file_node_data)
        for path, node_data in dir_nodes.items():
            await self._add_node_with_color(path, node_data, allow_expand=True)
        for path, node_data in file_nodes.items():
            await self._add_node_with_color(path, node_data, allow_expand=False)
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
            or event.node.data.path in store.cm_paths.man_dir_set
            or event.node.data.path in self.iterated_dirs
        ):
            return
        self._add_unmanaged_dir_children(event.node.data)
