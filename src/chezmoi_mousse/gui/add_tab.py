from collections.abc import Iterable
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalGroup
from textual.reactive import reactive
from textual.widgets import DirectoryTree, Switch

from chezmoi_mousse import (
    AppType,
    AreaName,
    Chars,
    Switches,
    Tcss,
    TreeName,
    ViewName,
)

from .shared.operate.contents_view import ContentsView
from .shared.switch_slider import SwitchSlider
from .shared.tabs_base import TabsBase

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["AddTab", "FilteredDirTree"]


class FilteredDirTree(DirectoryTree, AppType):

    class UnwantedDirs(StrEnum):
        bin = "bin"
        CMakeFiles = "CMakeFiles"
        Crash_Reports = "Crash Reports"
        DerivedData = "DerivedData"
        Desktop = "Desktop"
        Documents = "Documents"
        dot_build = ".build"
        dot_bundle = ".bundle"
        dot_dart_tool = ".dart_tool"
        dot_DS_Store = ".DS_Store"
        dot_env = ".env"
        dot_git = ".git"
        dot_ipynb_checkpoints = ".ipynb_checkpoints"
        dot_mozilla = ".mozilla"
        dot_mypy_cache = ".mypy_cache"
        dot_parcel_cache = ".parcel_cache"
        dot_pytest_cache = ".pytest_cache"
        dot_ssh = ".ssh"
        dot_Trash = ".Trash"
        dot_venv = ".venv"
        Downloads = "Downloads"
        extensions = "extensions"
        go_build = "go-build"
        Music = "Music"
        node_modules = "node_modules"
        Pictures = "Pictures"
        Public = "Public"
        Recent = "Recent"
        temp = "temp"
        Temp = "Temp"
        Templates = "Templates"
        tmp = "tmp"
        trash = "trash"
        Trash = "Trash"
        Videos = "Videos"

    class UnwantedFileExtensions(StrEnum):
        AppImage = ".AppImage"
        bak = ".bak"
        bin = ".bin"
        coverage = ".coverage"
        doc = ".doc"
        docx = ".docx"
        egg_info = ".egg-info"
        exe = ".exe"
        gz = ".gz"
        img = ".img"
        iso = ".iso"
        jar = ".jar"
        kdbx = ".kdbx"
        lock = ".lock"
        pdf = ".pdf"
        pid = ".pid"
        ppt = ".ppt"
        pptx = ".pptx"
        rar = ".rar"
        swp = ".swp"
        tar = ".tar"
        temp = ".temp"
        tgz = ".tgz"
        tmp = ".tmp"
        seven_zip = ".7z"
        xls = ".xls"
        xlsx = ".xlsx"
        zip = ".zip"

    ICON_NODE_EXPANDED = Chars.down_triangle
    ICON_NODE = Chars.right_triangle
    ICON_FILE = " "

    unmanaged_dirs: reactive[bool] = reactive(False, init=False)
    unwanted: reactive[bool] = reactive(False, init=False)

    def on_mount(self) -> None:
        self.add_class(Tcss.dir_tree_widget.name, Tcss.border_title_top.name)
        self.border_title = " destDir "
        self.guide_depth = 3
        self.show_root = False

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:

        # Switches: Red - Red (default)
        if self.unmanaged_dirs is False and self.unwanted is False:
            return (
                p
                for p in paths
                if (
                    p.is_dir(follow_symlinks=False)
                    and not self._is_unwanted_dir(p)
                    and p in self.app.chezmoi.managed_dirs
                    and self._has_unmanaged_paths_in(p)
                )
                or (
                    p.is_file(follow_symlinks=False)
                    and not self._is_unwanted_file(p)
                    and (
                        p.parent in self.app.chezmoi.managed_dirs
                        or p.parent == self.path
                    )
                    and p not in self.app.chezmoi.managed_files
                )
            )
        # Switches: Green - Red
        elif self.unmanaged_dirs is True and self.unwanted is False:
            return (
                p
                for p in paths
                if (
                    p.is_dir(follow_symlinks=False)
                    and not self._is_unwanted_dir(p)
                    and self._has_unmanaged_paths_in(p)
                )
                or (
                    p.is_file(follow_symlinks=False)
                    and not self._is_unwanted_file(p)
                    and (
                        p.parent in self.app.chezmoi.managed_dirs
                        or p.parent == self.path
                    )
                    and p not in self.app.chezmoi.managed_files
                )
            )
        # Switches: Red - Green
        elif self.unmanaged_dirs is False and self.unwanted is True:
            return (
                p
                for p in paths
                if (
                    p.is_dir(follow_symlinks=False)
                    and p in self.app.chezmoi.managed_dirs
                    and self._has_unmanaged_paths_in(p)
                )
                or (
                    p.is_file(follow_symlinks=False)
                    and p not in self.app.chezmoi.managed_files
                    and (
                        p.parent in self.app.chezmoi.managed_dirs
                        or p.parent == self.path
                    )
                )
            )
        # Switches: Green - Green, include all unmanaged paths
        else:
            return (
                p
                for p in paths
                if (
                    p.is_file(follow_symlinks=False)
                    and p not in self.app.chezmoi.managed_files
                )
                or (
                    p.is_dir(follow_symlinks=False)
                    and self._has_unmanaged_paths_in(p)
                )
            )

    def _has_unmanaged_paths_in(self, dir_path: Path) -> bool:
        # check if the directory its children contain unmanaged paths
        return any(
            p
            for p in dir_path.iterdir()
            if p not in self.app.chezmoi.managed_dirs
            and p not in self.app.chezmoi.managed_files
        )

    def _is_unwanted_dir(self, dir_path: Path) -> bool:
        try:
            FilteredDirTree.UnwantedDirs(dir_path.name)
            return True
        except ValueError:
            if "cache" in dir_path.name.lower():
                return True
            return False

    def _is_unwanted_file(self, file_path: Path) -> bool:
        extension = file_path.suffix
        try:
            FilteredDirTree.UnwantedFileExtensions(extension)
            return True
        except ValueError:
            if "cache" in file_path.name.lower():
                return True
            return False


class AddTab(TabsBase, AppType):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(ids=self.ids)

    def compose(self) -> ComposeResult:
        with VerticalGroup(
            id=self.ids.tab_vertical_id(area=AreaName.left),
            classes=Tcss.tab_left_vertical.name,
        ):
            yield FilteredDirTree(
                Path.home(), id=self.ids.tree_id(tree=TreeName.add_tree)
            )
        with Vertical(id=self.ids.tab_vertical_id(area=AreaName.right)):
            yield ContentsView(ids=self.ids)

        yield SwitchSlider(
            ids=self.ids, switches=(Switches.unmanaged_dirs, Switches.unwanted)
        )

    @on(DirectoryTree.DirectorySelected)
    @on(DirectoryTree.FileSelected)
    def update_contents_view_and_title(
        self,
        event: DirectoryTree.DirectorySelected | DirectoryTree.FileSelected,
    ) -> None:
        event.stop()
        assert event.node.data is not None
        contents_view = self.query_one(
            self.ids.view_id("#", view=ViewName.contents_view), ContentsView
        )
        contents_view.path = event.node.data.path
        contents_view.border_title = f" {event.node.data.path} "

    @on(Switch.Changed)
    def handle_filter_switches(self, event: Switch.Changed) -> None:
        event.stop()
        tree = self.query_one(
            self.ids.tree_id("#", tree=TreeName.add_tree), FilteredDirTree
        )
        if event.switch.id == self.ids.switch_id(
            switch=Switches.unmanaged_dirs.value
        ):
            tree.unmanaged_dirs = event.value
        elif event.switch.id == self.ids.switch_id(
            switch=Switches.unwanted.value
        ):
            tree.unwanted = event.value
        tree.reload()
