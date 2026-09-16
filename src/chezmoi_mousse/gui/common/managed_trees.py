from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual.widgets import (
    Tree,
)

from chezmoi_mousse import store
from chezmoi_mousse.data_classes import ChezmoiPaths
from chezmoi_mousse.str_enums import (
    ColorVar,
    Tcss,
)

if TYPE_CHECKING:
    from textual import getters
    from textual.widgets.tree import TreeNode

    from chezmoi_mousse.gui.textual_app import ChezmoiGui


__all__ = ["ChezmoiTree", "ManagedTree", "StatusTree"]


class _ManagedTreeBase(Tree[Path]):
    """Base class for the managed tree with unchanged paths, without unchanged paths,
    and with unmanaged or unwanted paths."""

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(self) -> None:
        self.node_color_map: dict[Path, str] = {}
        self.node_map: dict[Path, TreeNode[Path]] = {}
        self.cm_paths = ChezmoiPaths.empty()
        super().__init__(
            label="root",
            classes=Tcss.managed_tree,
        )

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

    def should_include_dir(self, _path: Path) -> bool:
        return True

    def should_include_file(self, _path: Path, _status: str) -> bool:
        return True

    async def update_tree(self, cm_paths: ChezmoiPaths) -> None:
        self.cm_paths = cm_paths

        for path in cm_paths.managed_dirs:
            if self.should_include_dir(path):
                self.add_node(path, allow_expand=True)

        for path, status in cm_paths.managed_files.items():
            if self.should_include_file(path, status):
                self.add_node(path, allow_expand=False)


class ManagedTree(_ManagedTreeBase):
    def on_mount(self) -> None:
        super().on_mount()
        self.display = False

    def should_include_dir(self, path: Path) -> bool:
        return path not in self.cm_paths.sets.clean_space_dirs

    def should_include_file(self, _: Path, status: str) -> bool:
        return status != "xx"


class StatusTree(_ManagedTreeBase):
    def on_mount(self) -> None:
        super().on_mount()
        self.display = True

    def should_include_dir(self, path: Path) -> bool:
        return path not in self.cm_paths.sets.clean_space_dirs

    def should_include_file(self, _: Path, status: str) -> bool:
        return status != "  "


class ChezmoiTree(_ManagedTreeBase):
    def on_mount(self) -> None:
        super().on_mount()
        self.display = False

    def should_include_dir(self, path: Path) -> bool:
        return path not in self.cm_paths.sets.clean_space_dirs

    def should_include_file(self, _: Path, status: str) -> bool:
        return status != "  "
