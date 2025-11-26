from collections.abc import Iterable
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Button, DirectoryTree, Switch

from chezmoi_mousse import (
    AppType,
    Chars,
    DirTreeNodeData,
    OperateBtn,
    PathKind,
    Tcss,
)
from chezmoi_mousse.shared import (
    ContentsView,
    CurrentAddNodeMsg,
    OperateButtons,
)

from .common.switch_slider import SwitchSlider

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["AddTab", "FilteredDirTree"]


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
    gif = ".gif"
    gz = ".gz"
    img = ".img"
    iso = ".iso"
    jar = ".jar"
    jpeg = ".jpeg"
    jpg = ".jpg"
    kdbx = ".kdbx"
    lock = ".lock"
    pdf = ".pdf"
    pid = ".pid"
    png = ".png"
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


class FilteredDirTree(DirectoryTree, AppType):

    ICON_NODE_EXPANDED = Chars.down_triangle
    ICON_NODE = Chars.right_triangle
    ICON_FILE = " "

    unmanaged_dirs: reactive[bool] = reactive(False, init=False)
    unwanted: reactive[bool] = reactive(False, init=False)

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:

        # Switches: Red - Red (default)
        if self.unmanaged_dirs is False and self.unwanted is False:
            return (
                p
                for p in paths
                if (
                    p.is_dir(follow_symlinks=False)
                    and not self._is_unwanted_dir(p)
                    and p in self.app.chezmoi.dirs
                    and self._has_unmanaged_paths_in(p)
                )
                or (
                    p.is_file(follow_symlinks=False)
                    and not self._is_unwanted_file(p)
                    and (
                        p.parent in self.app.chezmoi.dirs
                        or p.parent == self.path
                    )
                    and p not in self.app.chezmoi.files
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
                        p.parent in self.app.chezmoi.dirs
                        or p.parent == self.path
                    )
                    and p not in self.app.chezmoi.files
                )
            )
        # Switches: Red - Green
        elif self.unmanaged_dirs is False and self.unwanted is True:
            return (
                p
                for p in paths
                if (
                    p.is_dir(follow_symlinks=False)
                    and p in self.app.chezmoi.dirs
                    and self._has_unmanaged_paths_in(p)
                )
                or (
                    p.is_file(follow_symlinks=False)
                    and p not in self.app.chezmoi.files
                    and (
                        p.parent in self.app.chezmoi.dirs
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
                    p.is_dir(follow_symlinks=False)
                    and self._has_unmanaged_paths_in(p)
                )
                or (
                    p.is_file(follow_symlinks=False)
                    and p not in self.app.chezmoi.files
                )
            )

    def _has_unmanaged_paths_in(self, dir_path: Path) -> bool:
        # Assume a directory with more than max_entries is not of interest
        max_entries = 300
        try:
            for idx, p in enumerate(dir_path.iterdir(), start=1):
                if idx > max_entries:
                    return False
                elif (
                    p not in self.app.chezmoi.dirs
                    and p not in self.app.chezmoi.files
                ):
                    return True
            return True
        except (PermissionError, OSError):
            return False

    def _is_unwanted_dir(self, dir_path: Path) -> bool:
        try:
            UnwantedDirs(dir_path.name)
            return True
        except ValueError:
            if "cache" in dir_path.name.lower():
                return True
            return False

    def _is_unwanted_file(self, file_path: Path) -> bool:
        extension = file_path.suffix
        try:
            UnwantedFileExtensions(extension)
            return True
        except ValueError:
            if "cache" in file_path.name.lower():
                return True
            return False


class AddTab(Horizontal, AppType):

    destDir: Path

    def __init__(self, ids: "AppIds") -> None:
        super().__init__()
        self.ids = ids

    def compose(self) -> ComposeResult:
        yield FilteredDirTree(
            self.destDir, id=self.app.tab_ids.add.tree.dir_tree
        )
        yield ContentsView(ids=self.ids)
        yield OperateButtons(
            ids=self.ids, buttons=(OperateBtn.add_file, OperateBtn.add_dir)
        )
        yield SwitchSlider(ids=self.ids)

    def on_mount(self) -> None:
        contents_view = self.query_one(
            self.ids.logger.contents_q, ContentsView
        )
        contents_view.add_class(Tcss.border_title_top.name)
        contents_view.border_title = f" {self.destDir} "
        dir_tree = self.query_one(
            self.app.tab_ids.add.tree.dir_tree_q, FilteredDirTree
        )
        dir_tree.guide_depth = 3
        dir_tree.show_root = False
        dir_tree.add_class(
            Tcss.tab_left_vertical.name, Tcss.border_title_top.name
        )
        dir_tree.border_title = f" {self.destDir} "

    def update_buttons(self, is_dir: bool) -> None:
        add_file_button = self.query_one(
            self.ids.operate_btn.add_file_q, Button
        )
        add_dir_button = self.query_one(self.ids.operate_btn.add_dir_q, Button)
        if is_dir is True:
            add_file_button.disabled = True
            add_file_button.tooltip = OperateBtn.add_file.disabled_tooltip
            add_dir_button.disabled = False
            add_dir_button.tooltip = OperateBtn.add_dir.enabled_tooltip
        else:
            add_file_button.disabled = False
            add_file_button.tooltip = OperateBtn.add_file.enabled_tooltip
            add_dir_button.disabled = True
            add_dir_button.tooltip = OperateBtn.add_dir.disabled_tooltip
        return

    def send_message_current_add_node(
        self, path: Path, path_kind: "PathKind"
    ) -> None:
        message_data = DirTreeNodeData(path=path, path_kind=path_kind)
        self.post_message(CurrentAddNodeMsg(message_data))

    @on(DirectoryTree.DirectorySelected)
    @on(DirectoryTree.FileSelected)
    def update_contents_view_and_send_message(
        self,
        event: DirectoryTree.DirectorySelected | DirectoryTree.FileSelected,
    ) -> None:
        event.stop()
        if event.node.data is None:
            self.app.notify(
                f"AddTab: TreeNode data is None for {event.node.label}",
                severity="error",
            )
            return
        contents_view = self.query_one(
            self.ids.logger.contents_q, ContentsView
        )
        contents_view.path = event.node.data.path
        contents_view.border_title = f" {event.node.data.path} "

        if isinstance(event, DirectoryTree.FileSelected):
            self.update_buttons(is_dir=False)
            self.send_message_current_add_node(
                path=event.node.data.path, path_kind=PathKind.FILE
            )
        else:
            self.update_buttons(is_dir=True)
            self.send_message_current_add_node(
                path=event.node.data.path, path_kind=PathKind.DIR
            )

    @on(Switch.Changed)
    def handle_filter_switches(self, event: Switch.Changed) -> None:
        event.stop()
        tree = self.query_one(
            self.app.tab_ids.add.tree.dir_tree_q, FilteredDirTree
        )
        if event.switch.id == self.ids.filter.unmanaged_dirs:
            tree.unmanaged_dirs = event.value
        elif event.switch.id == self.ids.filter.unwanted:
            tree.unwanted = event.value
        tree.reload()
