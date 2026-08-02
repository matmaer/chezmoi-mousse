from __future__ import annotations

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
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

__all__ = ["FilteredDirTree"]

GIT_OBJECT_DIR: str = f"{os.sep}{Path(".git", "objects")}{os.sep}"


class FilteredDirTree(DirectoryTree):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded
    ICON_FILE = " "

    show_managed: reactive[bool] = reactive(False, init=False)
    show_unwanted: reactive[bool] = reactive(False, init=False)

    def __init__(self, *, dest_dir: Path) -> None:
        super().__init__(dest_dir)
        self.root.expand()
        self.root.allow_expand = False  # prevent from being collapsed

    def on_mount(self) -> None:
        self.guide_depth: int = 3
        self.border_title = " destDir tree "

    def _should_show_path(self, is_managed: bool, is_unwanted: bool) -> bool:
        # Pass one to determine if a path should POTENTIALLY be displayed based on the
        # filter state

        filter_state = (self.show_managed, self.show_unwanted)

        match filter_state:
            case (False, False):  # show_managed is OFF, show_unwanted is OFF
                # Never show path if is_managed is True
                # Show the path if is_managed is False and is_unwanted is False
                return not is_managed and not is_unwanted

            case (True, False):  # show_managed is ON, show_unwanted is OFF
                # Always show the path if is_managed is True
                # Show the path if is_managed is False and is_unwanted is False
                return is_managed or not is_unwanted

            case (False, True):  # show_managed is OFF, show_unwanted is ON
                # Never show the path if is_managed is True
                # Show the path if is_managed is False and is_unwanted is True or False
                return not is_managed

            case (True, True):  # show_managed is ON, show_unwanted is ON
                return True  # Always show the path, no second pass needed

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        filter_paths: set[Path] = set()
        for p in paths:
            is_dir = p.is_dir()
            is_managed = bool(
                p in self.app.cmattr.paths.managed_dirs
                or p in self.app.cmattr.paths.managed_files
            )
            if is_dir:
                is_unwanted = CheckPath.is_unwanted_dir(p)
            else:
                is_unwanted = CheckPath.is_unwanted_file(p)
            if self._should_show_path(is_managed, is_unwanted):
                filter_paths.add(p)
        return filter_paths
