from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from subprocess import CompletedProcess, run
from typing import Literal

from chezmoi_mousse import PathDict

__all__ = [
    "ChangeCmd",
    "Chezmoi",
    "GlobalCmd",
    "ManagedStatusData",
    "ReadCmd",
    "ReadVerbs",
    "VerbArgs",
]


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

    managed_dirs: str = ""  # stdout from ReadCmd.managed_dirs
    managed_files: str = ""  # stdout from ReadCmd.managed_files
    status_dirs: str = ""  # stdout from ReadCmd.status_dirs
    status_files: str = ""  # stdout from ReadCmd.status_files

    @property
    def managed_dir_paths(self) -> list[Path]:
        return [Path(line) for line in self.managed_dirs.splitlines()]

    @property
    def managed_file_paths(self) -> list[Path]:
        return [Path(line) for line in self.managed_files.splitlines()]

    @property
    def all_file_paths_with_status(self) -> PathDict:
        return {
            Path(line[3:]): line[:2] for line in self.status_files.splitlines()
        }

    @property
    def all_dir_paths_with_status(self) -> PathDict:
        return {
            Path(line[3:]): line[:2] for line in self.status_dirs.splitlines()
        }

    def paths_with_status(
        self,
        operation_type: Literal["apply", "re_add"],
        path_type: Literal["files", "dirs"],
    ) -> PathDict:

        if path_type == "dirs" and operation_type == "apply":
            return {
                key: value[1]
                for key, value in self.all_dir_paths_with_status.items()
                if value[1] in "ADM"
            }
        elif path_type == "files" and operation_type == "apply":
            return {
                key: value[0]
                for key, value in self.all_file_paths_with_status.items()
                if value[0] in "ADM"
            }
        elif path_type == "dirs" and operation_type == "re_add":
            return {
                key: value[0]
                for key, value in self.all_dir_paths_with_status.items()
                if value[0] == "M" or (value[0] == " " and value[1] == "M")
            }
        elif path_type == "files" and operation_type == "re_add":
            return {
                key: value[0]
                for key, value in self.all_file_paths_with_status.items()
                if value[0] == "M" or (value[0] == " " and value[1] == "M")
            }
        return {}


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
        self.managed_status_data = ManagedStatusData()

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

    def refresh_managed_status_data(self) -> ManagedStatusData:
        # get data from chezmoi managed stdout
        self.managed_status_data.managed_dirs = self.read(ReadCmd.managed_dirs)
        self.managed_status_data.managed_files = self.read(
            ReadCmd.managed_files
        )
        # get data from chezmoi status stdout
        self.managed_status_data.status_dirs = self.read(ReadCmd.status_dirs)
        self.managed_status_data.status_files = self.read(ReadCmd.status_files)
        return self.managed_status_data

    def child_files_with_status(
        self, pane_name: Literal["apply", "re_add"], dir_path: Path
    ) -> list[Path]:
        # only returns immediate subfiles
        paths_with_status = self.managed_status_data.paths_with_status(
            pane_name, "files"
        )
        return [p for p in paths_with_status if p.parent == dir_path]

    def has_any_child_file_with_status(
        self, pane_name: Literal["apply", "re_add"], dir_path: Path
    ) -> bool:
        return any(
            p
            for p in self.managed_status_data.managed_file_paths
            if p
            in self.managed_status_data.paths_with_status(pane_name, "files")
            and p.is_relative_to(dir_path)
        )

    def child_files_without_status(
        self, pane_name: Literal["apply", "re_add"], dir_path: Path
    ) -> list[Path]:
        paths_with_status = self.managed_status_data.paths_with_status(
            pane_name, "files"
        )
        return [
            p
            for p in self.managed_status_data.managed_file_paths
            if p not in paths_with_status and p.parent == dir_path
        ]

    def has_any_child_file_without_status(
        self, pane_name: Literal["apply", "re_add"], dir_path: Path
    ) -> bool:
        return any(
            p
            for p in self.managed_status_data.managed_file_paths
            if p
            not in self.managed_status_data.paths_with_status(
                pane_name, "files"
            )
            and p.is_relative_to(dir_path)
        )

    def managed_child_dirs_in(self, dir_path: Path) -> list[Path]:
        # only returns immediate subdirs
        return [
            p
            for p in self.managed_status_data.managed_dir_paths
            if p.parent == dir_path
        ]
