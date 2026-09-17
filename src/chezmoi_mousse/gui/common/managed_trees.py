from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.widgets import (
    Tree,
)

from chezmoi_mousse import store
from chezmoi_mousse.gui.common.messages import TreeStateMsg
from chezmoi_mousse.str_enums import (
    ColorVar,
    StatusCode as Sc,
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
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(self, tree_name: TreeName) -> None:
        self.node_map: NodeMap = {}

        super().__init__(label="root", classes=Tcss.managed_tree, name=tree_name)

    def on_mount(self) -> None:
        self.root.data = store.cfg.dest_dir_path
        self.guide_depth = 3
        self.show_root = False
        self.dir_color_map: dict[str, str] = {
            # D combos
            Sc.DA: ColorVar.text_error,
            Sc.DD: ColorVar.bogus,  # probably impossible status pair
            Sc.DM: ColorVar.text_error,
            Sc.DS: ColorVar.text_error,
            # M combos
            Sc.MA: ColorVar.text_warning,
            Sc.MD: ColorVar.text_error,
            Sc.MM: ColorVar.text_warning,
            Sc.MS: ColorVar.text_warning,
            # S combos
            Sc.SA: ColorVar.text_success,
            Sc.SD: ColorVar.text_error,
            Sc.SM: ColorVar.text_warning,
            # Meta codes
            Sc.SS: ColorVar.foreground_darken_2,
            Sc.TT: ColorVar.text_primary,
            Sc.UU: ColorVar.text_accent,
        }
        self.file_color_map: dict[str, str] = {
            # D combos
            Sc.DA: ColorVar.error,
            Sc.DD: ColorVar.bogus,  # probably impossible status pair
            Sc.DM: ColorVar.error,
            Sc.DS: ColorVar.error,
            # M combos
            Sc.MA: ColorVar.warning,
            Sc.MD: ColorVar.error,
            Sc.MM: ColorVar.warning,
            Sc.MS: ColorVar.warning,
            # S combos
            Sc.SA: ColorVar.success,
            Sc.SD: ColorVar.error,
            Sc.SM: ColorVar.warning,
            # Meta codes
            Sc.SS: ColorVar.dimmed,
            Sc.TT: ColorVar.primary,
            Sc.UU: ColorVar.accent,
        }

    def color_label(self, path: Path, status: Sc, directory: bool) -> str:
        color_var = ColorVar.dimmed  # the default
        if directory:
            color_var = self.dir_color_map.get(status, ColorVar.bogus)
        else:
            color_var = self.file_color_map.get(status, ColorVar.bogus)
        italic = " italic" if path in store.cm_path_sets.missing else ""
        color = self.app.theme_variables.get(color_var, ColorVar.bogus.value)
        return f"[{color}{italic}]{path.name}[/]"

    def add_node(self, path: Path, status: Sc, *, allow_expand: bool) -> None:
        parent_node = self.node_map.get(path.parent, self.root)
        label = self.color_label(path, status, allow_expand)
        new_node = parent_node.add(label=label, data=path, allow_expand=allow_expand)
        self.node_map[path] = new_node

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


class ChezmoiTree(_ManagedTreeBase):
    def __init__(self) -> None:
        super().__init__(tree_name=TreeName.chezmoi_tree)

    def on_mount(self) -> None:
        super().on_mount()
        self.display = False

    async def update_tree(self) -> None:
        for path, status in store.cm_paths.all_dirs.items():
            self.add_node(path, status, allow_expand=True)
        for path, status in store.cm_paths.all_files.items():
            self.add_node(path, status, allow_expand=False)


class ManagedTree(_ManagedTreeBase):
    def __init__(self) -> None:
        super().__init__(tree_name=TreeName.managed_tree)

    def on_mount(self) -> None:
        super().on_mount()
        self.display = False

    async def update_tree(self) -> None:
        for path, status in store.cm_paths.managed_dirs.items():
            self.add_node(path, status, allow_expand=True)
        for path, status in store.cm_paths.managed_files.items():
            self.add_node(path, status, allow_expand=False)


class StatusTree(_ManagedTreeBase):
    def __init__(self) -> None:
        super().__init__(tree_name=TreeName.status_tree)

    def on_mount(self) -> None:
        super().on_mount()
        self.display = True

    async def update_tree(self) -> None:
        for path, status in store.cm_paths.status_dirs.items():
            self.add_node(path, status, allow_expand=True)
        for path, status in store.cm_paths.status_files.items():
            self.add_node(path, status, allow_expand=False)
