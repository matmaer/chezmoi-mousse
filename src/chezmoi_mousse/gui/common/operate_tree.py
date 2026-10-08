from __future__ import annotations

from typing import TYPE_CHECKING

from rich.markup import escape
from textual import on, work
from textual.widgets import Tree

from chezmoi_mousse import path_funcs, store
from chezmoi_mousse.data_types import NodeData
from chezmoi_mousse.str_enums import (
    ColorVar,
    StatusCode as Sc,
    TreeName,
)

if TYPE_CHECKING:
    from pathlib import Path

    from textual import getters
    from textual.widgets.tree import TreeNode

    from chezmoi_mousse.chezmoi_paths import CmPathChanges
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
        )

    def on_mount(self) -> None:
        self.iterated_dirs: set[Path] = set()
        self.display = False
        self.guide_depth = 3
        self.show_root = False
        self.root.data = store.cm_paths.dest_dir_node_data
        self.node_map: dict[Path, TreeNode[NodeData]] = {store.cfg.dest_dir: self.root}
        self._initial_tree_population()

    def _label_color_var(self, node_data: NodeData) -> ColorVar:
        status_code = node_data.status
        # TODO: check for missing or impossible status pairs
        mapping: dict[str | None, ColorVar] = {
            # D combos
            Sc.DA: ColorVar.text_warning,
            Sc.DD: ColorVar.text_error,
            Sc.DM: ColorVar.text_warning,
            Sc.DS: ColorVar.text_warning,
            # M combos
            Sc.MA: ColorVar.text_warning,
            Sc.MD: ColorVar.text_error,
            Sc.MM: ColorVar.text_warning,
            Sc.MS: ColorVar.text_warning,
            # S combos
            Sc.SA: ColorVar.text_warning,
            Sc.SD: ColorVar.text_error,
            Sc.SM: ColorVar.text_warning,
        }
        color_var: ColorVar = mapping.get(status_code, ColorVar.error_muted)
        is_man_tree = TreeName(self.name).is_managed_tree
        wanted = not node_data.un_wanted

        if node_data.dir_path:
            if node_data.has_status:
                return ColorVar.warning_lighten_3
            if node_data.has_nested_status and node_data.has_nested_unmanaged:
                return (
                    ColorVar.text_primary if is_man_tree else ColorVar.primary_darken_1
                )
            elif node_data.has_nested_status:
                return ColorVar.text_primary
            if node_data.managed:
                return ColorVar.foreground_darken_3 if is_man_tree else ColorVar.text
            if node_data.un_managed and wanted:
                return ColorVar.text_success
            if node_data.un_wanted:
                return ColorVar.text_accent
        else:
            if node_data.has_status:
                return color_var
            if node_data.managed:
                return ColorVar.foreground_darken_3
            if node_data.un_managed and wanted:
                return ColorVar.text_success
            if node_data.un_wanted:
                return ColorVar.text_accent

        return color_var

    def apply_changes(self, changes: CmPathChanges) -> None:
        for path in changes.remove_tree_dirs:
            node = self.node_map[path]
            node.remove()
        for path in changes.remove_tree_files:
            node = self.node_map[path]
            node.remove()
        for path in changes.remove_node_map_paths:
            del self.node_map[path]

        for path, node_data in changes.add_tree_dirs.items():
            self._add_node_with_color(path, node_data, allow_expand=True)

        for path, node_data in changes.add_tree_files.items():
            self._add_node_with_color(path, node_data, allow_expand=False)

        for path, node_data in changes.change_tree_dirs.items():
            self.node_map[path].remove()
            self._add_node_with_color(path, node_data, allow_expand=True)

        for path, node_data in changes.change_tree_files.items():
            self.node_map[path].remove()
            self._add_node_with_color(path, node_data, allow_expand=False)

        self._expand_xpd_nodes()
        self.refresh(layout=True)

    def _child_key(self, node: TreeNode[NodeData]) -> tuple[bool, str]:
        assert node.data is not None
        return (not node.allow_expand, str(node.data.path).lower())

    def _next_sibling(
        self, parent_node: TreeNode[NodeData], path: Path, *, allow_expand: bool
    ) -> TreeNode[NodeData] | None:
        """The child to insert the new node before, None to append."""
        path_str = str(path).lower()
        key = (not allow_expand, path_str)
        children = parent_node.children
        # nodes are normally added in sorted order, so appending is the common case
        if not children or self._child_key(children[-1]) < key:
            return None
        return next(c for c in children if self._child_key(c) > key)

    def _add_node_with_color(
        self, path: Path, node_data: NodeData, *, allow_expand: bool
    ) -> None:
        if path == store.cfg.dest_dir:
            return
        parent_node = self.node_map[node_data.path.parent]
        italic = " italic" if not node_data.exists else ""
        color = self.app.theme_variables[self._label_color_var(node_data)]
        node_label = f"[{color}{italic}]{escape(path.name)}[/]"

        new_node = parent_node.add(
            label=node_label,
            data=node_data,
            before=self._next_sibling(parent_node, path, allow_expand=allow_expand),
            allow_expand=allow_expand,
        )
        self.node_map[path] = new_node

    def _expand_xpd_nodes(self) -> None:
        if TreeName(self.name).is_xpd_tree:
            for node in self.node_map.values():
                if node.data is not None and node.data.managed:
                    node.expand()

    @work
    async def _initial_tree_population(self) -> None:

        def get_tree_nodes(node_dict: dict[Path, NodeData]) -> dict[Path, NodeData]:
            result: dict[Path, NodeData] = {}
            for path, node_data in node_dict.items():
                if node_data.include_in_tree(TreeName(self.name)):
                    result[path] = node_data
            return path_funcs.sort_path_dict(result)

        dir_nodes = get_tree_nodes(store.cm_paths.dir_node_data)
        file_nodes = get_tree_nodes(store.cm_paths.file_node_data)

        for path, node_data in dir_nodes.items():
            self._add_node_with_color(path, node_data, allow_expand=True)
        for path, node_data in file_nodes.items():
            self._add_node_with_color(path, node_data, allow_expand=False)
        self._expand_xpd_nodes()
        if self.name == TreeName.managed_sp:
            self.display = True

    @on(Tree.NodeExpanded)
    def populate_un_managed_dir(self, event: Tree.NodeExpanded[NodeData]) -> None:
        event.stop()
        node_data = event.node.data
        if (
            node_data is None
            or node_data.dest_dir
            or node_data.managed
            or node_data.file_path
            or node_data.path in self.iterated_dirs
        ):
            return
        iter_dir_result: IterDirResult = path_funcs.get_un_man_children(node_data.path)
        for path, node_data in iter_dir_result.dirs.items():
            self._add_node_with_color(path, node_data, allow_expand=True)
        for path, node_data in iter_dir_result.files.items():
            self._add_node_with_color(path, node_data, allow_expand=False)
