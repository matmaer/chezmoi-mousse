from __future__ import annotations

from typing import TYPE_CHECKING

from rich.markup import escape
from rich.style import Style
from textual import on, work
from textual.widgets import Tree

from chezmoi_mousse import path_funcs, store
from chezmoi_mousse.data_types import NodeData
from chezmoi_mousse.str_enums import ColorVar, StatusCode as Sc, TreeName

if TYPE_CHECKING:
    from pathlib import Path

    from rich.text import Text
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
        super().__init__(id=tree_id, label="root", name=tree_name.value)

    def on_mount(self) -> None:
        self.iterated_dirs: set[Path] = set()
        self.display = False
        self.guide_depth = 3
        self.show_root = False
        self.root.data = store.cm_paths.dest_dir_node_data
        self.node_map: dict[Path, TreeNode[NodeData]] = {store.cfg.dest_dir: self.root}
        self._initial_tree_population()

    def render_label(
        self, node: TreeNode[NodeData], base_style: Style, style: Style
    ) -> Text:
        """Override render_label for a cursor node so the label keeps its own color and
        just underlines the cursor node.
        """
        if self.cursor_node is node:
            style = Style(underline=True)
        return super().render_label(node, base_style, style)

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

        if node_data.status_path:
            return color_var
        elif (
            node_data.status is None
            and node_data.managed
            and not node_data.dir_data.nested_status
        ):
            return ColorVar.foreground_darken_3
        elif node_data.dir_path:
            if node_data.dir_data.nested_status and node_data.dir_data.nested_wanted:
                return (
                    ColorVar.text_primary if is_man_tree else ColorVar.primary_darken_1
                )
            elif node_data.dir_data.nested_status:
                return ColorVar.text_primary
            if node_data.managed:
                return ColorVar.foreground_darken_3 if is_man_tree else ColorVar.text
            if node_data.un_managed and node_data.wanted:
                return ColorVar.text_success
            elif not node_data.wanted:
                return ColorVar.text_accent
        else:
            if node_data.managed:
                return ColorVar.foreground_darken_3
            elif node_data.wanted:
                return ColorVar.text_success
            elif not node_data.wanted:
                return ColorVar.text_accent

        return color_var

    async def update_nodes(self, changes: CmPathChanges) -> None:
        for path in changes.remove_tree_dirs | changes.remove_tree_files:
            if path in self.node_map:
                self._remove_node(path)

        tree_name = TreeName(self.name)

        for path, node_data in changes.add_tree_dirs.items():
            if node_data.include_in_tree(tree_name):
                self._add_node_with_color(path, node_data, allow_expand=True)

        for path, node_data in changes.add_tree_files.items():
            if node_data.include_in_tree(tree_name):
                self._add_node_with_color(path, node_data, allow_expand=False)

        self._apply_changed_nodes(
            changes.change_tree_dirs, tree_name, allow_expand=True
        )
        self._apply_changed_nodes(
            changes.change_tree_files, tree_name, allow_expand=False
        )

        self._expand_xpd_nodes()
        self.refresh(layout=True)

    def _apply_changed_nodes(
        self, changed: dict[Path, NodeData], tree_name: TreeName, *, allow_expand: bool
    ) -> None:
        for path, node_data in changed.items():
            if path == store.cfg.dest_dir:
                self.root.data = node_data
                continue
            in_tree = path in self.node_map
            include = node_data.include_in_tree(tree_name)
            if in_tree and include:
                node = self.node_map[path]
                node.data = node_data
                node.set_label(self._node_label(node_data))
            elif in_tree:
                self._remove_node(path)
            elif include:
                self._add_node_with_color(path, node_data, allow_expand=allow_expand)

    def _remove_node(self, path: Path) -> None:
        self.node_map[path].remove()
        removed_paths = [p for p in self.node_map if p == path or path in p.parents]
        for removed_path in removed_paths:
            del self.node_map[removed_path]
            self.iterated_dirs.discard(removed_path)

    def _get_before_node(
        self, parent_node: TreeNode[NodeData], node_data: NodeData
    ) -> TreeNode[NodeData] | None:
        file_nodes = [c for c in parent_node.children if not c.allow_expand]
        if node_data.dir_path:
            dir_nodes = [c for c in parent_node.children if c.allow_expand]
            for child in dir_nodes:
                if (
                    child.data is not None
                    and node_data.path.name.lower() < child.data.path.name.lower()
                ):
                    return child
            if file_nodes:
                return file_nodes[0]
        else:
            for child in file_nodes:
                if (
                    child.data is not None
                    and node_data.path.name.lower() < child.data.path.name.lower()
                ):
                    return child
        return None

    def _node_label(self, node_data: NodeData) -> str:
        italic = " italic" if not node_data.exists else ""
        color = self.app.theme_variables[self._label_color_var(node_data)]
        return f"[{color}{italic}]{escape(node_data.path.name)}[/]"

    def _add_node_with_color(
        self, path: Path, node_data: NodeData, *, allow_expand: bool
    ) -> None:
        if path == store.cfg.dest_dir:
            return
        parent_node = self.node_map[node_data.path.parent]
        new_node = parent_node.add(
            label=self._node_label(node_data),
            data=node_data,
            before=self._get_before_node(parent_node, node_data),
            allow_expand=allow_expand,
        )
        self.node_map[path] = new_node

    def _expand_xpd_nodes(self) -> None:
        if TreeName(self.name).is_xpd_tree:
            with self.prevent(Tree.NodeExpanded):
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
            return result

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
            or node_data.dir_data.dest_dir
            or node_data.managed
            or node_data.file_path
            or node_data.path in self.iterated_dirs
        ):
            return
        iter_dir_result: IterDirResult = path_funcs.get_un_man_children(node_data.path)
        self.iterated_dirs.add(node_data.path)
        for path, node_data in iter_dir_result.dirs.items():
            if TreeName(self.name).is_wanted_tree and not node_data.wanted:
                continue
            self._add_node_with_color(path, node_data, allow_expand=True)
        for path, node_data in iter_dir_result.files.items():
            if TreeName(self.name).is_wanted_tree and not node_data.wanted:
                continue
            self._add_node_with_color(path, node_data, allow_expand=False)
