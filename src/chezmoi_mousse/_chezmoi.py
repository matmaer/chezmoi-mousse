from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from subprocess import CompletedProcess, run
from typing import TYPE_CHECKING

from chezmoi_mousse._names import Canvas

if TYPE_CHECKING:
    from chezmoi_mousse._names import ActiveCanvas

    from .gui.logs_tab import AppLog, DebugLog, OutputLog

type PathDict = dict[Path, str]

__all__ = [
    "ChangeCmd",
    "Chezmoi",
    "GlobalCmd",
    "ManagedPaths",
    "ReadCmd",
    "ReadVerbs",
    "VerbArgs",
]


class GlobalCmd(Enum):
    default_args = [
        "--color=off",
        "--force",
        "--interactive=false",
        "--mode=file",
        "--no-pager",
        "--no-tty",
        "--progress=false",
    ]
    live_run = ["chezmoi"] + default_args
    dry_run = live_run + ["--dry-run"]


class VerbArgs(Enum):
    # encrypt = "--encrypt"
    format_json = "--format=json"
    git_log = [
        "--",
        "--no-pager",
        "log",
        "--date-order",
        "--format=%ar by %cn;%s",
        "--max-count=50",
        "--no-color",
        "--no-decorate",
        "--no-expand-tabs",
    ]
    include_dirs = "--include=dirs"
    include_files = "--include=files"
    path_style_absolute = "--path-style=absolute"
    reverse = "--reverse"


class ReadVerbs(Enum):
    cat = "cat"
    cat_config = "cat-config"
    data = "data"
    diff = "diff"
    doctor = "doctor"
    dump_config = "dump-config"
    git = "git"
    ignored = "ignored"
    managed = "managed"
    source_path = "source-path"
    status = "status"


class ReadCmd(Enum):
    cat = GlobalCmd.live_run.value + [ReadVerbs.cat.value]
    cat_config = GlobalCmd.live_run.value + [ReadVerbs.cat_config.value]
    diff = GlobalCmd.live_run.value + [ReadVerbs.diff.value]
    diff_reverse = GlobalCmd.live_run.value + [
        ReadVerbs.diff.value,
        VerbArgs.reverse.value,
    ]
    doctor = GlobalCmd.live_run.value + [ReadVerbs.doctor.value]
    dump_config = GlobalCmd.live_run.value + [
        VerbArgs.format_json.value,
        ReadVerbs.dump_config.value,
    ]
    git_log = (
        GlobalCmd.live_run.value
        + [ReadVerbs.git.value]
        + VerbArgs.git_log.value
    )
    ignored = GlobalCmd.live_run.value + [ReadVerbs.ignored.value]
    managed = GlobalCmd.live_run.value + [
        ReadVerbs.managed.value,
        VerbArgs.path_style_absolute.value,
    ]
    managed_dirs = GlobalCmd.live_run.value + [
        ReadVerbs.managed.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_dirs.value,
    ]
    managed_files = GlobalCmd.live_run.value + [
        ReadVerbs.managed.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_files.value,
    ]
    source_path = GlobalCmd.live_run.value + [ReadVerbs.source_path.value]
    status_paths = GlobalCmd.live_run.value + [
        ReadVerbs.status.value,
        VerbArgs.path_style_absolute.value,
    ]
    status_dirs = GlobalCmd.live_run.value + [
        ReadVerbs.status.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_dirs.value,
    ]
    status_files = GlobalCmd.live_run.value + [
        ReadVerbs.status.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_files.value,
    ]
    template_data = GlobalCmd.live_run.value + [ReadVerbs.data.value]


class ChangeCmd(Enum):
    add = ["add"]
    # add_encrypt = ["add", VerbArgs.encrypt.value]
    apply = ["apply"]
    # destroy = ["destroy"]
    # forget = ["forget"]
    init = ["init"]
    # purge = ["purge"]
    re_add = ["re-add"]


class Utils:
    @staticmethod
    def strip_stdout(stdout: str):
        # remove trailing and leading new lines but NOT leading whitespace
        stripped = stdout.lstrip("\n").rstrip()
        # remove intermediate empty lines
        return "\n".join(
            [line for line in stripped.splitlines() if line.strip() != ""]
        )


@dataclass
class ManagedPaths:
    managed_dirs_stdout: str = ""  # ReadCmd.managed_dirs
    managed_files_stdout: str = ""  # ReadCmd.managed_files
    status_dirs_stdout: str = ""  # ReadCmd.status_dirs
    status_files_stdout: str = ""  # ReadCmd.status_files
    status_paths_stdout: str = ""  # ReadCmd.status_paths

    # internal caches (populated lazily)
    _apply_status_files: PathDict | None = None
    _apply_status_paths: PathDict | None = None
    _managed_dirs: list[Path] | None = None
    _managed_files: list[Path] | None = None
    _re_add_status_files: PathDict | None = None
    _re_add_status_paths: PathDict | None = None
    _status_paths_dict: PathDict | None = None

    def clear_cache(self) -> None:
        # called in the Chezmoi.refresh_managed_paths_data() method
        self._apply_status_files = None
        self._apply_status_paths = None
        self._managed_dirs = None
        self._managed_files = None
        self._re_add_status_files = None
        self._re_add_status_paths = None
        self._status_paths_dict = None

    @property
    def managed_dirs(self) -> list[Path]:
        if self._managed_dirs is None:
            self._managed_dirs = [
                Path(line) for line in self.managed_dirs_stdout.splitlines()
            ]
        return self._managed_dirs

    @property
    def managed_files(self) -> list[Path]:
        if self._managed_files is None:
            self._managed_files = [
                Path(line) for line in self.managed_files_stdout.splitlines()
            ]
        return self._managed_files

    @property
    def all_status_paths(self) -> PathDict:
        if self._status_paths_dict is None:
            self._status_paths_dict = {
                Path(line[3:]): line[:2]
                for line in self.status_paths_stdout.splitlines()
            }
        return self._status_paths_dict

    @property
    def apply_status_paths(self) -> PathDict:
        if self._apply_status_paths is None:
            self._apply_status_paths = {
                path: status_pair[1]
                for path, status_pair in self.all_status_paths.items()
                if status_pair[1] in "ADM"  # Check second character only
            }
        return self._apply_status_paths

    @property
    def re_add_status_paths(self) -> PathDict:
        # Consider paths with a status for apply operations but no status
        # for re-add operations to have a status if they exist, handled later.
        if self._re_add_status_paths is None:
            self._re_add_status_paths = {
                path: status_pair[0]
                for path, status_pair in self.all_status_paths.items()
                if status_pair[0] == "M"
                or (status_pair[0] == " " and status_pair[1] in "ADM")
            }
        return self._re_add_status_paths

    @property
    def apply_status_files(self) -> PathDict:
        if self._apply_status_files is None:
            self._apply_status_files = {
                path: status_code
                for path, status_code in self.apply_status_paths.items()
                if path in self.managed_files
            }
        return self._apply_status_files

    @property
    def re_add_status_files(self) -> PathDict:
        # consider these files to always have status M
        # Existence for re-add operations will be checked later on.
        if self._re_add_status_files is None:
            self._re_add_status_files = {
                key: "M"
                for key, _ in self.re_add_status_paths.items()
                if key in self.managed_files
            }
        return self._re_add_status_files


class Chezmoi:

    def __init__(self, *, changes_enabled: bool, dev_mode: bool) -> None:

        self._changes_enabled = changes_enabled
        self.managed_paths = ManagedPaths()
        self.app_log: AppLog | None = None
        self.output_log: OutputLog | None = None
        if dev_mode is True:
            self.debug_log: DebugLog | None = None

    #################################
    # Command execution and logging #
    #################################

    def _log_in_app_and_output_log(self, result: CompletedProcess[str]):
        result.stdout = Utils.strip_stdout(result.stdout)
        if self.app_log is not None and self.output_log is not None:
            self.app_log.completed_process(result)
            self.output_log.completed_process(result)

    def read(self, read_cmd: ReadCmd, path: Path | None = None) -> str:
        command: list[str] = read_cmd.value
        if path is not None:
            command: list[str] = command + [str(path)]
        if read_cmd == ReadCmd.doctor:
            time_out = 3
        else:
            time_out = 1
        result: CompletedProcess[str] = run(
            command,
            capture_output=True,
            shell=False,
            text=True,
            timeout=time_out,
        )
        self._log_in_app_and_output_log(result)
        return Utils.strip_stdout(result.stdout)

    def perform(
        self, change_sub_cmd: ChangeCmd, change_arg: str | None = None
    ) -> None:
        if self._changes_enabled is True:
            base_cmd: list[str] = GlobalCmd.live_run.value
        else:
            base_cmd: list[str] = GlobalCmd.dry_run.value
        command: list[str] = base_cmd + change_sub_cmd.value

        if change_arg is not None:
            command: list[str] = command + [change_arg]

        self._log_in_app_and_output_log(
            run(
                command, capture_output=True, shell=False, text=True, timeout=5
            )
        )

    def refresh_managed_paths_data(self):
        # get data from chezmoi managed stdout
        self.managed_paths.managed_dirs_stdout = self.read(
            ReadCmd.managed_dirs
        )
        self.managed_paths.managed_files_stdout = self.read(
            ReadCmd.managed_files
        )
        # get data from chezmoi status stdout
        self.managed_paths.status_dirs_stdout = self.read(ReadCmd.status_dirs)
        self.managed_paths.status_files_stdout = self.read(
            ReadCmd.status_files
        )
        self.managed_paths.status_paths_stdout = self.read(
            ReadCmd.status_paths
        )
        # clear internal caches
        self.managed_paths.clear_cache()

    @property
    def managed_dirs(self) -> list[Path]:
        return self.managed_paths.managed_dirs

    @property
    def managed_files(self) -> list[Path]:
        return self.managed_paths.managed_files

    @property
    def _apply_status_paths(self) -> PathDict:
        return self.managed_paths.apply_status_paths

    @property
    def _re_add_status_paths(self) -> PathDict:
        return self.managed_paths.re_add_status_paths

    @property
    def _apply_status_files(self) -> PathDict:
        return self.managed_paths.apply_status_files

    @property
    def _re_add_status_files(self) -> PathDict:
        return self.managed_paths.re_add_status_files

    def all_status_files(self, active_canvas: "ActiveCanvas") -> PathDict:
        if active_canvas == Canvas.apply:
            return self._apply_status_files
        else:
            return self._re_add_status_files

    def status_files_in(
        self, active_canvas: "ActiveCanvas", dir_path: Path
    ) -> PathDict:
        if active_canvas == Canvas.apply:
            return {
                path: status
                for path, status in self._apply_status_paths.items()
                if path.parent == dir_path and path in self.managed_files
            }
        else:
            return {
                path: status
                for path, status in self._re_add_status_paths.items()
                if path.parent == dir_path
                and path in self.managed_files
                and path.exists()
            }

    def status_dirs_in(
        self, active_canvas: "ActiveCanvas", dir_path: Path
    ) -> PathDict:
        if active_canvas == Canvas.apply:
            result = {
                path: status
                for path, status in self._apply_status_paths.items()
                if path.parent == dir_path and path in self.managed_dirs
            }
            # Add dirs that contain status files but don't have direct status
            for path in self.managed_dirs:
                if (
                    path.parent == dir_path
                    and path not in result
                    and self._has_apply_status_files_in(path)
                ):
                    result[path] = " "
            return dict(sorted(result.items()))
        else:
            result = {
                path: status
                for path, status in self._re_add_status_paths.items()
                if path.parent == dir_path
                and path in self.managed_dirs
                and path.exists()
            }
            # Add dirs that contain status files but don't have direct status
            for path in self.managed_dirs:
                if (
                    path.parent == dir_path
                    and path not in result
                    and path.exists()
                    and self._has_re_add_status_files_in(path)
                ):
                    result[path] = " "
            return dict(sorted(result.items()))

    def files_without_status_in(
        self, active_canvas: "ActiveCanvas", dir_path: Path
    ) -> PathDict:
        if active_canvas == Canvas.apply:
            return {
                path: "X"
                for path in self.managed_files
                if path.parent == dir_path
                and path not in self._apply_status_paths
            }
        else:
            return {
                path: "X"
                for path in self.managed_files
                if path.parent == dir_path
                and path not in self._re_add_status_paths
                and path.exists()
            }

    def dirs_without_status_in(
        self, active_canvas: "ActiveCanvas", dir_path: Path
    ) -> PathDict:
        if active_canvas == Canvas.apply:
            status_paths = self._apply_status_paths
            has_status_check = self._has_apply_status_files_in
        else:
            status_paths = self._re_add_status_paths
            has_status_check = self._has_re_add_status_files_in

        result = {
            path: "X"
            for path in self.managed_dirs
            if path.parent == dir_path
            and path not in status_paths
            and not has_status_check(path)
        }
        # For re_add canvas, filter out non-existing directories
        if active_canvas == Canvas.re_add:
            result = {
                path: status
                for path, status in result.items()
                if path.exists()
            }
        return result

    def has_status_paths_in(
        self, active_canvas: "ActiveCanvas", dir_path: Path
    ) -> bool:
        if active_canvas == Canvas.apply:
            return self._has_apply_status_files_in(dir_path)
        else:
            return self._has_re_add_status_files_in(dir_path)

    def _has_apply_status_files_in(self, dir_path: Path) -> bool:
        return any(
            path.is_relative_to(dir_path) and path in self.managed_files
            for path in self._apply_status_paths.keys()
        )

    def _has_re_add_status_files_in(self, dir_path: Path) -> bool:
        # Create this list without calling exists()
        potential_files = [
            path
            for path in self._re_add_status_paths.keys()
            if path.is_relative_to(dir_path) and path in self.managed_files
        ]
        # Check if any of the potential files exist
        return any(path.exists() for path in potential_files)
