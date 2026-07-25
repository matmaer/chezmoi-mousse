import os
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from textual import getters
from textual.reactive import reactive
from textual.widgets import DirectoryTree

from chezmoi_mousse.functions import CheckPath
from chezmoi_mousse.str_enums import Chars

if TYPE_CHECKING:
    from chezmoi_mousse.cm_types import ChezmoiGui

__all__ = ["FilteredDirTree"]

GIT_OBJECT_DIR: str = f"{os.sep}{Path(".git", "objects")}{os.sep}"

# lightweight functions only needing a file or dir path, regardless of filter settings,
# only returning a bool


class FilteredDirTree(DirectoryTree):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded
    ICON_FILE = " "

    hide_unmanaged_dirs: reactive[bool] = reactive(False, init=False)
    show_managed: reactive[bool] = reactive(False, init=False)
    show_unwanted: reactive[bool] = reactive(False, init=False)

    def on_mount(self) -> None:
        self.guide_depth: int = 3
        self.border_title = " destDir tree "

    def _is_unwanted_file(self, file_path: Path) -> bool:
        return (
            CheckPath.is_bad_suffix(file_path)
            or CheckPath.is_large(file_path)
            or CheckPath.is_binary(file_path)
        )

    def _is_unwanted_dir(self, dir_path: Path) -> bool:
        return CheckPath.is_unwanted_dir_name(dir_path) or CheckPath.has_many_children(
            dir_path
        )

    def _show_file(self, file_path: Path) -> bool:

        if CheckPath.is_sensitive(file_path):
            return False

        if file_path in self.app.cm_attr.paths.managed_files:
            return self.hide_unmanaged_dirs

        if (
            file_path.parent not in self.app.cm_attr.paths.managed_dirs
            and self.hide_unmanaged_dirs is True
        ):
            return False

        return self._is_unwanted_file(file_path)

    def _show_dir(self, dir_path: Path) -> bool:

        if dir_path not in self.app.cm_attr.paths.managed_dirs:
            return not self.hide_unmanaged_dirs

        return True

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:

        return (
            p
            for p in paths
            if (self.show_unwanted and CheckPath.looks_like_cache(p))
            or (p.is_dir(follow_symlinks=False) and self._show_dir(p))
            or (p.is_file(follow_symlinks=False) and self._show_file(p))
        )
