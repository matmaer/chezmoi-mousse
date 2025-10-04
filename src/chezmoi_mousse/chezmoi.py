import json
import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from shutil import which
from subprocess import CompletedProcess, run
from typing import Literal

from chezmoi_mousse.id_typing import ParsedJson, PathDict, SplashReturnData
from chezmoi_mousse.id_typing.enums import TabName

# TODO: implement 'chezmoi verify', if exit 0, display message in Tree
# widgets inform the user why the Tree widget is empty
# TODO: implement spinner for commands taking a bit longer like operations


CHEZMOI_CMD = "chezmoi"


class GlobalCmd(Enum):
    chezmoi = [CHEZMOI_CMD]
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
    dir_status_lines = GlobalCmd.live_run.value + [
        ReadVerbs.status.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_dirs.value,
    ]
    doctor = GlobalCmd.live_run.value + [ReadVerbs.doctor.value]
    dump_config = GlobalCmd.live_run.value + [
        VerbArgs.format_json.value,
        ReadVerbs.dump_config.value,
    ]
    file_status_lines = GlobalCmd.live_run.value + [
        ReadVerbs.status.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_files.value,
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
    managed_tree = GlobalCmd.live_run.value + [
        ReadVerbs.managed.value,
        VerbArgs.tree.value,
    ]
    source_path = GlobalCmd.live_run.value + [ReadVerbs.source_path.value]


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
class DirPathStatus:
    path: Path
    status: str


@dataclass
class FilePathStatus:
    path: Path
    status: str


@dataclass
class ManagedStatus:

    dirs: list[Path] = field(default_factory=list[Path])
    files: list[Path] = field(default_factory=list[Path])
    status_dirs: list[DirPathStatus] = field(
        default_factory=list[DirPathStatus]
    )
    status_files: list[FilePathStatus] = field(
        default_factory=list[FilePathStatus]
    )


# app_log = AppLog()
# output_log = OutputLog()


class Chezmoi:

    def __init__(self) -> None:
        # will send string to callback, not list of strings, it's just the Callable signature
        self.debug_log: Callable[[str], None] | None = None
        self.app_log: Callable[[CompletedProcess[str]], None] | None = None
        self.output_log: Callable[[CompletedProcess[str]], None] | None = None
        # self.app_log = app_log
        # self.output_log = output_log

        self.chezmoi_found = (
            which(CHEZMOI_CMD) is not None
            and os.environ.get("PRETEND_CHEZMOI_NOT_FOUND") != "1"
        )
        self.changes_enabled: bool = (
            os.environ.get("MOUSSE_ENABLE_CHANGES") == "1"
        )
        self.config_dump = {}
        self.dev_mode: bool = os.environ.get("CHEZMOI_MOUSSE_DEV") == "1"
        self.config_dump: ParsedJson | None = None
        self.destDir: Path = Path.home()
        self.git_autoadd: bool = False
        self.git_autocommit: bool = False
        self.git_autopush: bool = False
        self.managed = ManagedStatus()
        self.sourceDir: Path = Path(tempfile.gettempdir())
        if self.chezmoi_found:
            result: CompletedProcess[str] = run(
                ReadCmd.dump_config.value,
                capture_output=True,
                shell=False,
                text=True,  # returns stdout as str instead of bytes
            )
            self.config_dump = json.loads(result.stdout)
            if self.config_dump is not None:
                self.destDir = Path(self.config_dump["destDir"])
                self.sourceDir = Path(self.config_dump["sourceDir"])
                self.git_autoadd = self.config_dump["git"]["autoadd"]
                self.git_autocommit = self.config_dump["git"]["autocommit"]
                self.git_autopush = self.config_dump["git"]["autopush"]

    # COMMAND TYPES

    @property
    def _read_cmd(self) -> type[ReadCmd]:
        return ReadCmd

    @property
    def _change_cmd(self) -> type[ChangeCmd]:
        return ChangeCmd

    # CACHED CHEZMOI CMD OUTPUTS

    @property
    def apply_dirs(self) -> PathDict:
        return self._create_status_dict(TabName.apply_tab, "dirs")

    @property
    def apply_files(self) -> PathDict:
        return self._create_status_dict(TabName.apply_tab, "files")

    @property
    def re_add_dirs(self) -> PathDict:
        return self._create_status_dict(TabName.re_add_tab, "dirs")

    @property
    def re_add_files(self) -> PathDict:
        return self._create_status_dict(TabName.re_add_tab, "files")

    # METHODS

    # def stripped_cmd(self, long_command: list[str]) -> str:
    #     return self.app_log.pretty_cmd_str(long_command)

    def _strip_stdout(self, stdout: str):
        # remove trailing and leading new lines but NOT leading whitespace
        stripped = stdout.lstrip("\n").rstrip()
        # remove intermediate empty lines
        return "\n".join(
            [line for line in stripped.splitlines() if line.strip()]
        )

    def _log_in_app_and_output_log(self, result: CompletedProcess[str]):
        result.stdout = self._strip_stdout(result.stdout)
        if self.app_log is not None:
            self.app_log(result)
        if self.output_log is not None:
            self.output_log(result)

    def read(self, read_cmd: ReadCmd, path: Path | None = None) -> str:
        command: list[str] = read_cmd.value
        if path is not None:
            command: list[str] = command + [str(path)]
        # CompletedProcess type arg is str as we use text=True
        result: CompletedProcess[str] = run(
            command, capture_output=True, shell=False, text=True, timeout=1
        )
        self._log_in_app_and_output_log(result)
        if self.debug_log is not None:
            self.debug_log(f"run {command}")
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

    def refresh_managed(
        self, splash_data: SplashReturnData | None = None
    ) -> None:
        if splash_data is not None:
            self.managed.dirs = [
                Path(line) for line in splash_data.managed_dirs.splitlines()
            ]
            self.managed.files = [
                Path(line) for line in splash_data.managed_files.splitlines()
            ]
            self.managed.status_dirs = [
                DirPathStatus(Path(line[3:]), line[:2])
                for line in splash_data.dir_status_lines.splitlines()
            ]
            self.managed.status_files = [
                FilePathStatus(Path(line[3:]), line[:2])
                for line in splash_data.file_status_lines.splitlines()
            ]
            return
        # get data from chezmoi managed stdout
        self.managed.dirs = [
            Path(line) for line in self.read(ReadCmd.managed_dirs).splitlines()
        ]
        self.managed.files = [
            Path(line)
            for line in self.read(ReadCmd.managed_files).splitlines()
        ]
        # get data from chezmoi status stdout
        self.managed.status_dirs = [
            DirPathStatus(Path(line[3:]), line[:2])
            for line in self.read(ReadCmd.dir_status_lines).splitlines()
        ]
        self.managed.status_files = [
            FilePathStatus(Path(line[3:]), line[:2])
            for line in self.read(ReadCmd.file_status_lines).splitlines()
        ]

    def files_with_status_in(
        self, tab_name: TabName, dir_path: Path
    ) -> list[Path]:
        files_dict: PathDict = {}
        if tab_name == TabName.apply_tab:
            files_dict = self.apply_files
        elif tab_name == TabName.re_add_tab:
            files_dict = self.re_add_files
        return [
            p
            for p, status in files_dict.items()
            if status != "X" and p.parent == dir_path
        ]

    def files_without_status_in(
        self, tab_name: TabName, dir_path: Path
    ) -> list[Path]:
        files_dict: PathDict = {}
        if tab_name == TabName.apply_tab:
            files_dict = self.apply_files
        elif tab_name == TabName.re_add_tab:
            files_dict = self.re_add_files
        return [
            p
            for p, status in files_dict.items()
            if status == "X" and p.parent == dir_path
        ]

    def managed_dirs_in(self, dir_path: Path) -> list[Path]:
        # checks only direct children
        return [p for p in self.managed.dirs if p.parent == dir_path]

    def _create_status_dict(
        self,
        tab_name: Literal[TabName.apply_tab, TabName.re_add_tab],
        kind: Literal["dirs", "files"],
    ) -> PathDict:
        path_dict: PathDict = {}
        status_idx: int = 0
        status_codes: str = ""
        if kind == "dirs":
            managed_paths = self.managed.dirs
            status_lines = [
                p.status + " " + str(p.path) for p in self.managed.status_dirs
            ]
        elif kind == "files":
            managed_paths = self.managed.files
            status_lines = [
                p.status + " " + str(p.path) for p in self.managed.status_files
            ]

        if tab_name == TabName.apply_tab:
            status_codes = "ADM"
            status_idx = 1
        elif tab_name == TabName.re_add_tab:
            status_codes = "M"
            status_idx = 0

        paths_with_status_dict = {}
        if tab_name == TabName.re_add_tab:
            # For re_add_tab, include files with "M" at status_idx=0 OR
            # files with space at status_idx=0 AND "M" at status_idx=1
            for line in status_lines:
                if line[status_idx] in status_codes or (
                    line[status_idx] == " " and line[1] == "M"
                ):
                    paths_with_status_dict[Path(line[3:])] = (
                        line[status_idx]
                        if line[status_idx] != " "
                        else line[1]
                    )
        else:
            paths_with_status_dict = {
                Path(line[3:]): line[status_idx]
                for line in status_lines
                if line[status_idx] in status_codes
            }

        for path in managed_paths:
            if path in paths_with_status_dict:
                path_dict[path] = paths_with_status_dict[path]
            else:
                path_dict[path] = "X"
        return path_dict
