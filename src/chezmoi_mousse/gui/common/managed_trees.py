from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual import on, work
from textual.widgets import Tree

from chezmoi_mousse import path_funcs, store
from chezmoi_mousse.str_enums import ColorVar, LabelStr, StatusCode as Sc, Tcss

if TYPE_CHECKING:
    from textual import getters
    from textual.widgets.tree import TreeNode

    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.named_tuples import ScanDirResult


type NodeMap = dict[Path, TreeNode[Path]]


__all__ = ["OperateTree"]


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
        self.scanned_dirs: set[Path] = set()
        self.loading = True
        self.display = False
        self.root.data = store.cfg.dest_dir
        self.guide_depth = 3
        self.show_root = False
        self.initial_tree_population(self.dir_nodes, self.file_nodes)

    def _color_label(self, path: Path, status: Sc, directory: bool) -> str:
        color_var = status.dir_color if directory else status.file_color
        italic = " italic" if path in store.cm_paths.missing_managed else ""
        color = self.app.theme_variables.get(color_var, ColorVar.bogus.value)
        return f"[{color}{italic}]{path.name}[/]"

    def _add_node_with_color(
        self, path: Path, status: Sc, *, allow_expand: bool
    ) -> None:
        parent_node = self.node_map.get(path.parent, self.root)
        label = self._color_label(path, status, allow_expand)
        new_node = parent_node.add(label=label, data=path, allow_expand=allow_expand)
        self.node_map[path] = new_node

    @work
    async def initial_tree_population(
        self, dirs: dict[Path, Sc], files: dict[Path, Sc]
    ) -> None:
        for path, status in dirs.items():
            self._add_node_with_color(path, status, allow_expand=True)
        for path, status in files.items():
            self._add_node_with_color(path, status, allow_expand=False)
        if self.id in (
            store.op_ids.tree.managed_only_sp_xpd,
            store.op_ids.tree.managed_all_mp_xpd,
        ):
            self.root.expand_all()
        if self.id in (
            store.op_ids.tree.un_man_plus_sp_xpd,
            store.op_ids.tree.un_man_plus_amp_xpd,
            store.op_ids.tree.un_wanted_plus_sp_xpd,
            store.op_ids.tree.un_wanted_plus_amp_xpd,
        ):
            for path, node in self.node_map.items():
                if path in store.cm_paths.man_dir_set:
                    node.expand()

        if self.id == store.op_ids.tree.managed_only_sp:
            self.display = True
            self.select_node(self.root)
            self.unselect()  # otherwise it looks like the first node is selected
        self.loading = False

    @work
    async def _populate_unmanaged_node(self, node: TreeNode[Path]) -> None:
        assert isinstance(node.data, Path)
        scan_dir_result: ScanDirResult = path_funcs.os_scan_dir(node.data)
        self.scanned_dirs.add(node.data)
        for path, status in scan_dir_result.dirs.items():
            if status == Sc.UU:
                store.cm_paths.path_labels[path] = LabelStr.unmanaged_dir
            elif status == Sc.XX:
                store.cm_paths.path_labels[path] = LabelStr.unwanted_dir
            self._add_node_with_color(path, status, allow_expand=True)
        for path, status in scan_dir_result.files.items():
            if status == Sc.UU:
                store.cm_paths.path_labels[path] = LabelStr.unmanaged_file
            elif status == Sc.XX:
                store.cm_paths.path_labels[path] = LabelStr.unwanted_file
            self._add_node_with_color(path, status, allow_expand=False)

    @on(Tree.NodeExpanded)
    def populate_unmanaged_node(self, event: Tree.NodeExpanded[Path]) -> None:
        if (
            event.node.data == store.cfg.dest_dir
            or self.id
            in (
                store.op_ids.tree.managed_only_sp,
                store.op_ids.tree.managed_only_sp_xpd,
                store.op_ids.tree.managed_all_mp,
                store.op_ids.tree.managed_all_mp_xpd,
            )
            or event.node.data in self.scanned_dirs
            or event.node.data in store.cm_paths.status_dir_set
            or event.node.data in store.cm_paths.man_dir_set
        ):
            return
        self._populate_unmanaged_node(event.node)
