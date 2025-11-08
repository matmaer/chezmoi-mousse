from collections.abc import Iterable
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Button, DirectoryTree, Switch

from chezmoi_mousse import (
    AppType,
    Chars,
    ContainerName,
    DirTreeNodeData,
    OperateBtn,
    Switches,
    Tcss,
    TreeName,
    ViewName,
)

from .shared.buttons import AddOpButtons
from .shared.contents_view import ContentsView
from .shared.operate_msg import CurrentAddNodeMsg
from .shared.switch_slider import AddSwitchSlider
from .shared.tabs_base import TabsBase

if TYPE_CHECKING:
    from chezmoi_mousse import PathType

    from .shared.canvas_ids import CanvasIds

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


class AddTab(TabsBase):

    destdir: Path

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(ids=self.ids)

        self.add_file_btn_qid = self.ids.button_id(
            "#", btn=OperateBtn.add_file
        )
        self.add_dir_btn_qid = self.ids.button_id("#", btn=OperateBtn.add_dir)
        self.add_tree_qid = self.ids.tree_id("#", tree=TreeName.add_tree)
        self.contents_view_qid = self.ids.view_id(
            "#", view=ViewName.contents_view
        )

    def compose(self) -> ComposeResult:
        with Vertical(
            id=self.ids.tab_vertical_id(name=ContainerName.left_side),
            classes=Tcss.tab_left_vertical.name,
        ):
            yield FilteredDirTree(
                self.destdir, id=self.ids.tree_id(tree=TreeName.add_tree)
            )
        with Vertical(
            id=self.ids.tab_vertical_id(name=ContainerName.right_side)
        ):
            yield ContentsView(ids=self.ids)
        yield AddOpButtons(ids=self.ids)
        yield AddSwitchSlider(ids=self.ids)

    def update_buttons(self, is_dir: bool) -> None:
        add_file_button = self.query_one(self.add_file_btn_qid, Button)
        add_dir_button = self.query_one(self.add_dir_btn_qid, Button)
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
        self, path: Path, path_type: "PathType"
    ) -> None:
        message_data = DirTreeNodeData(path=path, path_type=path_type)
        self.post_message(CurrentAddNodeMsg(message_data))

    @on(DirectoryTree.DirectorySelected)
    @on(DirectoryTree.FileSelected)
    def update_contents_view_and_send_message(
        self,
        event: DirectoryTree.DirectorySelected | DirectoryTree.FileSelected,
    ) -> None:
        event.stop()
        assert event.node.data is not None
        contents_view = self.query_one(self.contents_view_qid, ContentsView)
        contents_view.path = event.node.data.path
        contents_view.border_title = f" {event.node.data.path} "

        if isinstance(event, DirectoryTree.FileSelected):
            self.update_buttons(is_dir=False)
            self.send_message_current_add_node(
                path=event.node.data.path, path_type="file"
            )
        else:
            self.update_buttons(is_dir=True)
            self.send_message_current_add_node(
                path=event.node.data.path, path_type="dir"
            )

    @on(Switch.Changed)
    def handle_filter_switches(self, event: Switch.Changed) -> None:
        event.stop()
        tree = self.query_one(self.add_tree_qid, FilteredDirTree)
        if event.switch.id == self.ids.switch_id(
            switch=Switches.unmanaged_dirs
        ):
            tree.unmanaged_dirs = event.value
        elif event.switch.id == self.ids.switch_id(switch=Switches.unwanted):
            tree.unwanted = event.value
        tree.reload()
