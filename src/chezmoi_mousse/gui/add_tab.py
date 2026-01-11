from collections.abc import Iterable
from enum import StrEnum
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import DirectoryTree, Switch

from chezmoi_mousse import IDS, AppType, Chars, PathKind, StatusCode, Tcss

from .common.actionables import OperateButtons, SwitchSlider
from .common.operate_mode import OperateMode
from .common.tabs_base import TabsBase
from .common.trees import NodeData
from .common.views import ContentsView

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

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded
    ICON_FILE = " "

    unmanaged_dirs: reactive[bool] = reactive(False, init=False)
    unwanted: reactive[bool] = reactive(False, init=False)

    def on_mount(self) -> None:
        self.guide_depth = 3
        self.show_root = False
        self.add_class(Tcss.tab_left_vertical, Tcss.border_title_top)
        self.border_title = " destDir "

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:

        # SwitchEnum: Red - Red (default)
        if self.unmanaged_dirs is False and self.unwanted is False:
            return (
                p
                for p in paths
                if (
                    p.is_dir(follow_symlinks=False)
                    and not self._is_unwanted_dir(p)
                    and p in self.app.managed.dirs
                    and self._has_unmanaged_paths_in(p)
                )
                or (
                    p.is_file(follow_symlinks=False)
                    and not self._is_unwanted_file(p)
                    and (p.parent in self.app.managed.dirs or p.parent == self.path)
                    and p not in self.app.managed.files
                    and self._file_of_interest(p)
                )
            )
        # SwitchEnum: Green - Red
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
                    and (p.parent in self.app.managed.dirs or p.parent == self.path)
                    and p not in self.app.managed.files
                    and self._file_of_interest(p)
                )
            )
        # SwitchEnum: Red - Green
        elif self.unmanaged_dirs is False and self.unwanted is True:
            return (
                p
                for p in paths
                if (
                    p.is_dir(follow_symlinks=False)
                    and p in self.app.managed.dirs
                    and self._has_unmanaged_paths_in(p)
                )
                or (
                    p.is_file(follow_symlinks=False)
                    and p not in self.app.managed.files
                    and (p.parent in self.app.managed.dirs or p.parent == self.path)
                    and self._file_of_interest(p)
                )
            )
        # SwitchEnum: Green - Green, include all unmanaged paths
        else:
            return (
                p
                for p in paths
                if (p.is_dir(follow_symlinks=False) and self._has_unmanaged_paths_in(p))
                or (
                    p.is_file(follow_symlinks=False)
                    and p not in self.app.managed.files
                    and self._file_of_interest(p)
                )
            )

    def _file_of_interest(self, file_path: Path) -> bool:
        try:
            # Check size first to avoid reading large files
            if file_path.stat().st_size > self.app.max_file_size:
                return False
            # Now read only first 8 KiB
            with open(file_path, "rb") as f:
                chunk = f.read(8192)
            return b"\x00" not in chunk
        except OSError:
            return False

    def _has_unmanaged_paths_in(self, dir_path: Path) -> bool:
        # Assume a directory with more than max_entries is not of interest
        max_entries = 300
        try:
            for idx, p in enumerate(dir_path.iterdir(), start=1):
                if idx > max_entries:
                    return False
                elif p not in self.app.managed.dirs and p not in self.app.managed.files:
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


class AddTab(TabsBase, AppType):

    def __init__(self) -> None:
        super().__init__(ids=IDS.add)
        self.current_node: "NodeData | None" = None

    def compose(self) -> ComposeResult:
        yield OperateMode(ids=IDS.add)
        yield SwitchSlider(ids=IDS.add)

    def on_mount(self) -> None:
        self.operate_mode_container = self.query_one(
            IDS.add.container.op_mode_q, OperateMode
        )
        if self.app.dest_dir is None:
            raise ValueError("self.app.dest_dir is None on AddTab mount")
        self.mount(
            Horizontal(
                FilteredDirTree(self.app.dest_dir, id=IDS.add.tree.dir_tree),
                ContentsView(ids=IDS.add),
            ),
            OperateButtons(IDS.add),
        )
        contents_view = self.query_one(IDS.add.container.contents_q, ContentsView)
        contents_view.add_class(Tcss.border_title_top)
        contents_view.border_title = f" {self.app.dest_dir} "

    @on(DirectoryTree.DirectorySelected)
    @on(DirectoryTree.FileSelected)
    def update_contents_view(
        self, event: DirectoryTree.DirectorySelected | DirectoryTree.FileSelected
    ) -> None:
        event.stop()
        if event.node.data is None:
            self.app.notify("Select a new node to operate on.")
            return
        contents_view = self.query_one(IDS.add.container.contents_q, ContentsView)
        contents_view.border_title = f" {event.node.data.path} "

        path_kind = (
            PathKind.DIR
            if isinstance(event, DirectoryTree.DirectorySelected)
            else PathKind.FILE
        )
        self.current_node = NodeData(
            found=True,
            path=event.node.data.path,
            status=StatusCode.unmanaged,
            path_kind=path_kind,
        )
        contents_view.node_data = self.current_node
        self.operate_mode_container.path_arg = self.current_node.path

    @on(Switch.Changed)
    def handle_filter_switches(self, event: Switch.Changed) -> None:
        event.stop()
        dir_tree = self.query_one(IDS.add.tree.dir_tree_q, FilteredDirTree)
        if event.switch.id == IDS.add.filter.unmanaged_dirs:
            dir_tree.unmanaged_dirs = event.value
        elif event.switch.id == IDS.add.filter.unwanted:
            dir_tree.unwanted = event.value
        dir_tree.reload()
