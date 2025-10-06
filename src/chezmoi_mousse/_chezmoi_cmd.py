from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from subprocess import CompletedProcess, run
from typing import Literal

from chezmoi_mousse._str_enums import PaneBtn

__all__ = [
    "ActiveTab",
    "ChangeCmd",
    "Chezmoi",
    "GlobalCmd",
    "ManagedStatusData",
    "PathDict",
    "ReadCmd",
    "ReadVerbs",
    "VerbArgs",
]

type PathDict = dict[Path, str]
type ActiveTab = Literal[PaneBtn.apply_tab, PaneBtn.re_add_tab]


class GlobalCmd(Enum):
    chezmoi = ["chezmoi"]
    default_args = [
        "--color=off",
        "--force",
        "--interactive=false",
        "--mode=file",
        "--no-pager",
        "--no-tty",
        "--progress=false",
    ]
    live_run = chezmoi + default_args
    dry_run = live_run + ["--dry-run"]


class VerbArgs(Enum):
    encrypt = "--encrypt"
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
    tree = "--tree"


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
    data = GlobalCmd.live_run.value + [ReadVerbs.data.value]
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
    status = GlobalCmd.live_run.value + [
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


class ChangeCmd(Enum):
    add = ["add"]
    add_encrypt = ["add", VerbArgs.encrypt.value]
    apply = ["apply"]
    destroy = ["destroy"]
    forget = ["forget"]
    init = ["init"]
    purge = ["purge"]
    re_add = ["re-add"]


@dataclass
class ManagedStatusData:

    managed_dirs_stdout: str = ""  # stdout from ReadCmd.managed_dirs
    managed_files_stdout: str = ""  # stdout from ReadCmd.managed_files
    status_dirs_stdout: str = ""  # stdout from ReadCmd.status_dirs
    status_files_stdout: str = ""  # stdout from ReadCmd.status_files
    status_paths_stdout: str = ""  # stdout from ReadCmd.status

    # PROPERTIES RETURNING ALL PATHS FOR A SUBSET

    @property
    def all_dirs(self) -> list[Path]:
        return [Path(line) for line in self.managed_dirs_stdout.splitlines()]

    @property
    def all_files(self) -> list[Path]:
        return [Path(line) for line in self.managed_files_stdout.splitlines()]

    @property
    def _all_status_paths_dict(self) -> PathDict:
        return {
            Path(line[3:]): line[:2]
            for line in self.status_paths_stdout.splitlines()
        }

    # PROPERTIES RETURNING ALL STATUS PATHS BY OPERATION TYPE

    # chezmoi status codes processed: A, D, M, or a space
    # "node status" codes:
    #   X (no status but managed)

    @property
    def _apply_status_paths(self) -> PathDict:
        return {
            (key): value[1]
            for key, value in self._all_status_paths_dict.items()
            if value in "ADM"
        }

    @property
    def _re_add_status_paths(self) -> PathDict:
        return {
            key: value[0]
            for key, value in self._all_status_paths_dict.items()
            if value[0] == "M" or (value[0] == " " and value[1] == "M")
        }

    def has_status_paths_in(
        self, active_tab: ActiveTab, dir_path: Path
    ) -> bool:
        if active_tab == PaneBtn.apply_tab:
            status_paths = self._apply_status_paths
        elif active_tab == PaneBtn.re_add_tab:
            status_paths = self._re_add_status_paths
        return any(key.is_relative_to(dir_path) for key in status_paths.keys())

    def dir_has_status(self, active_tab: ActiveTab, dir_path: Path) -> bool:
        if active_tab == PaneBtn.apply_tab:
            status_paths = self._apply_status_paths
        elif active_tab == PaneBtn.re_add_tab:
            status_paths = self._re_add_status_paths
        return dir_path in status_paths

    # FUNCTIONS RETURNING A LIST OF PATHS FOR IMMEDIATE CHILDREN

    def dirs_in(self, dir_path: Path) -> list[Path]:
        return [p for p in self.all_dirs if p.parent == dir_path]

    def files_in(self, dir_path: Path) -> list[Path]:
        return [p for p in self.all_files if p.parent == dir_path]

    def all_status_files(self, active_tab: ActiveTab) -> PathDict:
        if active_tab == PaneBtn.apply_tab:
            return {
                path: status
                for path, status in self._apply_status_paths.items()
                if path in self.all_files and status != "X"
            }
        else:
            return {
                path: status
                for path, status in self._re_add_status_paths.items()
                if path in self.all_files and status != "X"
            }

    def all_files_without_status(self, active_tab: ActiveTab) -> PathDict:
        if active_tab == PaneBtn.apply_tab:
            return {
                path: status
                for path, status in self._apply_status_paths.items()
                if path in self.all_files and status == "X"
            }
        else:
            return {
                path: status
                for path, status in self._re_add_status_paths.items()
                if path in self.all_files and status == "X"
            }

    def status_files_in(
        self, active_tab: ActiveTab, dir_path: Path
    ) -> PathDict:
        if active_tab == PaneBtn.apply_tab:
            return {
                path: status
                for path, status in self._apply_status_paths.items()
                if path.parent == dir_path and path in self.all_files
            }
        else:
            return {
                path: status
                for path, status in self._re_add_status_paths.items()
                if path.parent == dir_path and path in self.all_files
            }

    def status_dirs_in(
        self, active_tab: ActiveTab, dir_path: Path
    ) -> PathDict:
        if active_tab == PaneBtn.apply_tab:
            return {
                path: status
                for path, status in self._apply_status_paths.items()
                if path.parent == dir_path and path in self.all_dirs
            }
        else:
            return {
                path: status
                for path, status in self._re_add_status_paths.items()
                if path.parent == dir_path and path in self.all_dirs
            }

    def files_without_status_in(
        self, active_tab: ActiveTab, dir_path: Path
    ) -> PathDict:
        if active_tab == PaneBtn.apply_tab:
            return {
                path: "X"
                for path in self.all_files
                if path.parent == dir_path
                and path not in self._apply_status_paths
            }
        else:
            return {
                path: "X"
                for path in self.all_files
                if path.parent == dir_path
                and path not in self._re_add_status_paths
            }

    def dirs_without_status_in(
        self, active_tab: ActiveTab, dir_path: Path
    ) -> PathDict:
        if active_tab == PaneBtn.apply_tab:
            return {
                path: "X"
                for path in self.all_dirs
                if path.parent == dir_path
                and path not in self._apply_status_paths
            }
        else:
            return {
                path: "X"
                for path in self.all_dirs
                if path.parent == dir_path
                and path not in self._re_add_status_paths
            }

    # FUNCTION RETURNING THE STATUS CODE FOR A PATH

    def status_code(self, active_tab: ActiveTab, path: Path) -> str:
        # returns the status code for a given path
        # uses one of the properties above to get the status code depending on
        # the active_tab and path_types
        if active_tab == PaneBtn.apply_tab:
            return self._apply_status_paths[path]
        else:
            return self._re_add_status_paths[path]


class Chezmoi:

    def __init__(self, *, changes_enabled: bool) -> None:
        self.changes_enabled = changes_enabled

        self.call_app_log: Callable[[CompletedProcess[str]], None] | None = (
            None
        )
        self.call_output_log: (
            Callable[[CompletedProcess[str]], None] | None
        ) = None

        # We need to cache this for Tree widgets and update it after running
        # and update it after running related ChangeCmd commands
        self.managed_paths = ManagedStatusData()

    # COMMAND TYPES

    @property
    def _read_cmd(self) -> type[ReadCmd]:
        return ReadCmd

    @property
    def _change_cmd(self) -> type[ChangeCmd]:
        return ChangeCmd

    def _strip_stdout(self, stdout: str):
        # remove trailing and leading new lines but NOT leading whitespace
        stripped = stdout.lstrip("\n").rstrip()
        # remove intermediate empty lines
        return "\n".join(
            [line for line in stripped.splitlines() if line.strip()]
        )

    def _log_in_app_and_output_log(self, result: CompletedProcess[str]):
        result.stdout = self._strip_stdout(result.stdout)
        if self.call_app_log is not None:
            self.call_app_log(result)
        if self.call_output_log is not None:
            self.call_output_log(result)

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
        return self._strip_stdout(result.stdout)

    def perform(
        self, change_sub_cmd: ChangeCmd, change_arg: str | None = None
    ) -> None:
        if self.changes_enabled:
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

    def refresh_managed_paths_data(self) -> ManagedStatusData:
        # get data from chezmoi managed stdout
        self.managed_paths.managed_dirs_stdout = self.read(
            ReadCmd.managed_dirs
        )  # noqa: E501 #
        self.managed_paths.managed_files_stdout = self.read(
            ReadCmd.managed_files
        )
        # get data from chezmoi status stdout
        self.managed_paths.status_dirs_stdout = self.read(ReadCmd.status_dirs)
        self.managed_paths.status_files_stdout = self.read(
            ReadCmd.status_files
        )
        return self.managed_paths
