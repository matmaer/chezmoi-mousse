from collections.abc import Iterable
from enum import StrEnum
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Button, DirectoryTree, Static, Switch

from chezmoi_mousse import (
    IDS,
    AppType,
    Chars,
    NodeData,
    OpBtnLabels,
    OperateStrings,
    PathKind,
    Tcss,
)
from chezmoi_mousse._operate_button_data import OpBtnEnum
from chezmoi_mousse.shared import (
    CurrentAddNodeMsg,
    OperateButtonMsg,
    OperateButtons,
)

from .common.contents_view import ContentsView
from .common.switch_slider import SwitchSlider
from .common.tabs_base import TabsBase

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
        self.guide_depth = 3
        self.show_root = False
        self.add_class(Tcss.tab_left_vertical, Tcss.border_title_top)
        self.border_title = " destDir "

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:

        # Switches: Red - Red (default)
        if self.unmanaged_dirs is False and self.unwanted is False:
            return (
                p
                for p in paths
                if (
                    p.is_dir(follow_symlinks=False)
                    and not self._is_unwanted_dir(p)
                    and p in self.app.cmd.paths.dirs
                    and self._has_unmanaged_paths_in(p)
                )
                or (
                    p.is_file(follow_symlinks=False)
                    and not self._is_unwanted_file(p)
                    and (
                        p.parent in self.app.cmd.paths.dirs
                        or p.parent == self.path
                    )
                    and p not in self.app.cmd.paths.files
                    and self._file_of_interest(p)
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
                        p.parent in self.app.cmd.paths.dirs
                        or p.parent == self.path
                    )
                    and p not in self.app.cmd.paths.files
                    and self._file_of_interest(p)
                )
            )
        # Switches: Red - Green
        elif self.unmanaged_dirs is False and self.unwanted is True:
            return (
                p
                for p in paths
                if (
                    p.is_dir(follow_symlinks=False)
                    and p in self.app.cmd.paths.dirs
                    and self._has_unmanaged_paths_in(p)
                )
                or (
                    p.is_file(follow_symlinks=False)
                    and p not in self.app.cmd.paths.files
                    and (
                        p.parent in self.app.cmd.paths.dirs
                        or p.parent == self.path
                    )
                    and self._file_of_interest(p)
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
                    and p not in self.app.cmd.paths.files
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
                elif (
                    p not in self.app.cmd.paths.dirs
                    and p not in self.app.cmd.paths.files
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


class AddTab(TabsBase, AppType):

    destDir: Path | None = None

    def __init__(self) -> None:
        super().__init__(ids=IDS.add)
        self.current_node: "NodeData | None" = None

    def compose(self) -> ComposeResult:
        yield Static(id=IDS.add.static.operate_info, classes=Tcss.operate_info)
        yield SwitchSlider(ids=IDS.add)
        yield OperateButtons(ids=IDS.add)

    def on_mount(self) -> None:
        self.add_dir_button = self.query_one(
            IDS.add.operate_btn.add_dir_q, Button
        )
        self.add_dir_button.display = True
        self.add_file_button = self.query_one(
            IDS.add.operate_btn.add_file_q, Button
        )
        self.add_file_button.display = True
        self.exit_btn = self.query_one(
            IDS.add.operate_btn.operate_exit_q, Button
        )
        self.operate_info = self.query_one(
            IDS.add.static.operate_info_q, Static
        )
        self.operate_info.display = False
        if self.destDir is not None:
            self.mount(
                Horizontal(
                    FilteredDirTree(self.destDir, id=IDS.add.tree.dir_tree),
                    ContentsView(ids=IDS.add),
                )
            )
            self.contents_view = self.query_one(
                IDS.add.container.contents_q, ContentsView
            )
            self.contents_view.add_class(Tcss.border_title_top)
            self.contents_view.border_title = f" {self.destDir} "
            self.dir_tree = self.query_one(
                IDS.add.tree.dir_tree_q, FilteredDirTree
            )

    def run_operate_command(self) -> None:
        if self.current_node is None:
            return
        if self.current_node.path_kind == PathKind.DIR:
            write_cmd = OpBtnEnum.add_dir.write_cmd
        elif self.current_node.path_kind == PathKind.FILE:
            write_cmd = OpBtnEnum.add_file.write_cmd
        else:
            raise ValueError("Unknown path kind in run_operate_command.")
        operate_result = self.app.cmd.perform(
            write_cmd,
            path_arg=self.current_node.path,
            changes_enabled=self.app.changes_enabled,
        )
        self.add_dir_button.disabled = True
        if self.current_node.path_kind == PathKind.FILE:
            self.add_file_button.disabled = True
        else:
            self.add_dir_button.disabled = True
        if operate_result.dry_run is True:
            self.exit_btn.label = OpBtnLabels.cancel
        elif operate_result.dry_run is False:
            # self.dir_tree.reload()
            content_view = self.query_exactly_one(ContentsView)
            content_view.node_data = None
            content_view.node_data = self.current_node
            self.exit_btn.label = OpBtnLabels.reload
        self.operate_info.border_title = OperateStrings.cmd_output_subtitle
        if operate_result.exit_code == 0:
            self.operate_info.border_subtitle = OperateStrings.success_subtitle
            self.operate_info.add_class(Tcss.operate_success)
            self.operate_info.update(f"{operate_result.std_out}")
        else:
            self.operate_info.border_subtitle = OperateStrings.error_subtitle
            self.operate_info.add_class(Tcss.operate_error)
            self.operate_info.update(f"{operate_result.std_err}")

    @on(DirectoryTree.DirectorySelected)
    @on(DirectoryTree.FileSelected)
    def update_contents_view(
        self,
        event: DirectoryTree.DirectorySelected | DirectoryTree.FileSelected,
    ) -> None:
        event.stop()
        if event.node.data is None:
            self.app.notify("Select a new node to operate on.")
            return
        self.contents_view.border_title = f" {event.node.data.path} "

        path_kind = (
            PathKind.DIR
            if isinstance(event, DirectoryTree.DirectorySelected)
            else PathKind.FILE
        )
        if path_kind == PathKind.DIR:
            self.add_file_button.disabled = True
            self.add_dir_button.disabled = False
        elif path_kind == PathKind.FILE:
            self.add_file_button.disabled = False
            self.add_dir_button.disabled = True
        else:
            raise ValueError("Unknown path kind.")
        self.current_node = NodeData(
            found=True,
            path=event.node.data.path,
            status="",
            path_kind=path_kind,
        )
        self.contents_view.node_data = self.current_node

    def toggle_widget_visibility(self) -> None:
        # Widgets shown by default
        self.app.toggle_main_tabs_display()
        self.dir_tree.display = (
            False if self.dir_tree.display is True else True
        )
        self.operate_info.display = (
            True if self.operate_info.display is False else False
        )
        # Depending on self.app.operating_mode, show/hide buttons
        switch_slider = self.query_one(
            IDS.add.container.switch_slider_q, SwitchSlider
        )
        switch_slider.display = (
            False if self.app.operating_mode is True else True
        )
        if self.app.operating_mode is True:
            self.exit_btn.display = True
            switch_slider.display = False  # regardless of visibility
        else:
            self.exit_btn.display = False
            # this will restore the previous vilibility, whatever it was
            switch_slider.display = True

    def write_pre_operate_info(self) -> None:
        if self.current_node is None:
            return
        lines_to_write: list[str] = []
        if self.current_node.path_kind == PathKind.DIR:
            write_cmd = OpBtnEnum.add_dir.write_cmd
        elif self.current_node.path_kind == PathKind.FILE:
            write_cmd = OpBtnEnum.add_file.write_cmd
        else:
            raise ValueError("Unknown path kind in run_operate_command.")
        lines_to_write.append(
            f"{OperateStrings.ready_to_run}"
            f"[$text-warning]{write_cmd.pretty_cmd} "
            f"{self.current_node.path}[/]"
        )
        if self.app.changes_enabled is True:
            if self.git_autocommit is True:
                lines_to_write.append(OperateStrings.auto_commit)
            if self.git_autopush is True:
                lines_to_write.append(OperateStrings.auto_push)
        self.operate_info.border_subtitle = OperateStrings.add_subtitle
        self.operate_info.update("\n".join(lines_to_write))

    @on(OperateButtonMsg)
    def handle_button_pressed(self, msg: OperateButtonMsg) -> None:
        msg.stop()
        if self.current_node is None:
            raise ValueError("self.current_node is None")
        if self.current_node.path_kind == PathKind.DIR:
            self.add_file_button.display = False
        elif self.current_node.path_kind == PathKind.FILE:
            self.add_dir_button.display = False
        if msg.label in (
            OpBtnLabels.add_dir_review,
            OpBtnLabels.add_file_review,
        ):
            self.exit_btn.display = False
            self.app.operating_mode = True
            self.toggle_widget_visibility()
            if self.current_node.path_kind == PathKind.DIR:
                self.add_dir_button.label = OpBtnLabels.add_dir_run
            elif self.current_node.path_kind == PathKind.FILE:
                self.add_file_button.label = OpBtnLabels.add_file_run
            self.write_pre_operate_info()
        elif msg.label in (OpBtnLabels.add_file_run, OpBtnLabels.add_dir_run):
            self.run_operate_command()
        elif msg.label == OpBtnLabels.cancel:
            self.add_dir_button.display = True
            self.add_dir_button.label = OpBtnLabels.add_dir_review
            self.add_file_button.display = True
            self.add_file_button.label = OpBtnLabels.add_file_review
            self.app.operating_mode = False
            self.toggle_widget_visibility()
        elif msg.label == OpBtnLabels.reload:
            self.add_dir_button.display = True
            self.add_dir_button.label = OpBtnLabels.add_dir_review
            self.add_file_button.display = True
            self.add_file_button.label = OpBtnLabels.add_file_review
            self.app.operating_mode = False
            self.toggle_widget_visibility()

    @on(CurrentAddNodeMsg)
    def handle_new_apply_node_selected(self, msg: CurrentAddNodeMsg) -> None:
        msg.stop()
        self.current_node = msg.node_data

    @on(Switch.Changed)
    def handle_filter_switches(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == IDS.add.filter.unmanaged_dirs:
            self.dir_tree.unmanaged_dirs = event.value
        elif event.switch.id == IDS.add.filter.unwanted:
            self.dir_tree.unwanted = event.value
        self.dir_tree.reload()
