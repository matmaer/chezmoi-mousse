from collections.abc import Iterable
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalGroup
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

from .shared.operate.contents_and_diff import ContentsView
from .shared.switch_slider import SwitchSlider

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["AddTab", "FilteredDirTree"]


class FilteredDirTree(DirectoryTree, AppType):

    class UnwantedDirs(StrEnum):
        __pycache__ = "__pycache__"
        bin = "bin"
        cache = "cache"
        Cache = "Cache"
        CMakeFiles = "CMakeFiles"
        Crash_Reports = "Crash Reports"
        DerivedData = "DerivedData"
        Desktop = "Desktop"
        Documents = "Documents"
        dot_build = ".build"
        dot_bundle = ".bundle"
        dot_cache = ".cache"
        dot_dart_tool = ".dart_tool"
        dot_DS_Store = ".DS_Store"
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

    class UnwantedFiles(StrEnum):
        AppImage = ".AppImage"
        bak = ".bak"
        cache = ".cache"
        coverage = ".coverage"
        doc = ".doc"
        docx = ".docx"
        egg_info = ".egg-info"
        gz = ".gz"
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
        xls = ".xls"
        xlsx = ".xlsx"
        zip = ".zip"

    ICON_NODE_EXPANDED = Chars.down_triangle
    ICON_NODE = Chars.right_triangle
    ICON_FILE = " "

    unmanaged_dirs: reactive[bool] = reactive(False, init=False)
    unwanted: reactive[bool] = reactive(False, init=False)

    def has_unmanaged_files(self, dir_path: Path) -> bool:
        managed_child_files = [
            p for p in self.app.chezmoi.managed_files if p.parent == dir_path
        ]
        if managed_child_files == []:
            return False
        else:
            return True

    def has_unmanaged_dirs(self, dir_path: Path) -> bool:
        managed_child_dirs = [
            p for p in self.app.chezmoi.managed_dirs if p.parent == dir_path
        ]
        if managed_child_dirs == []:
            return False
        else:
            return True

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:

        managed_dirs = self.app.chezmoi.managed_dirs
        managed_files = self.app.chezmoi.managed_files

        # Switches: Red - Red (default)
        if self.unmanaged_dirs is False and self.unwanted is False:
            return (
                p
                for p in paths
                if (
                    p.is_file()
                    and (p.parent in managed_dirs or p.parent == self.path)
                    and not self._is_unwanted_path(p)
                    and p not in managed_files
                )
                or (
                    p.is_dir()
                    and not self._is_unwanted_path(p)
                    and p in managed_dirs
                )
            )
        # Switches: Green - Red
        elif self.unmanaged_dirs is True and self.unwanted is False:
            return (
                p
                for p in paths
                if p not in managed_files and not self._is_unwanted_path(p)
            )
        # Switches: Red - Green
        elif self.unmanaged_dirs is False and self.unwanted is True:
            return (
                p
                for p in paths
                if (
                    p.is_file()
                    and (p.parent in managed_dirs or p.parent == self.path)
                    and p not in managed_files
                )
                or (p.is_dir() and p in managed_dirs)
            )
        # Switches: Green - Green, include all unmanaged paths
        elif self.unmanaged_dirs is True and self.unwanted is True:
            return (
                p
                for p in paths
                if p.is_dir() or (p.is_file() and p not in managed_files)
            )
        else:
            return paths

    def _is_unwanted_path(self, path: Path) -> bool:
        if path.is_dir():
            try:
                FilteredDirTree.UnwantedDirs(path.name)
                return True
            except ValueError:
                pass
        if path.is_file():
            extension = path.suffix
            try:
                FilteredDirTree.UnwantedFiles(extension)
                return True
            except ValueError:
                pass
        return False


class AddTab(Horizontal, AppType):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.tab_container_id)

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

    def on_mount(self) -> None:
        contents_view = self.query_exactly_one(ContentsView)
        contents_view.add_class(Tcss.border_title_top.name)
        contents_view.border_title = " destDir "

        dir_tree = self.query_exactly_one(FilteredDirTree)
        dir_tree.add_class(
            Tcss.dir_tree_widget.name, Tcss.border_title_top.name
        )
        dir_tree.border_title = " destDir "
        dir_tree.show_root = False
        dir_tree.guide_depth = 3

    def on_directory_tree_file_selected(
        self, event: FilteredDirTree.FileSelected
    ) -> None:
        event.stop()

        assert event.node.data is not None
        contents_view = self.query_one(
            self.ids.view_id("#", view=ViewName.contents_view), ContentsView
        )
        contents_view.path = event.node.data.path
        contents_view.border_title = f" {event.node.data.path} "

    @on(FilteredDirTree.DirectorySelected)
    def update_contents_view_and_title(
        self, event: FilteredDirTree.DirectorySelected
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
