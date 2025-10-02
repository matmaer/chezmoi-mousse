import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from shutil import which
from subprocess import CompletedProcess, run
from typing import Literal

from rich.markup import escape
from textual.widgets import RichLog

import chezmoi_mousse.custom_theme as theme
from chezmoi_mousse.id_typing import ParsedJson, PathDict, SplashReturnData
from chezmoi_mousse.id_typing.enums import Chars, TabName, Tcss

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


class LogsEnum(Enum):
    app_log = " App Log "
    debug_log = " Debug Log "
    init_log = " Init Log "
    output_log = " Commands With Raw Stdout "


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


class CommandLogBase(RichLog):

    def _log_time(self) -> str:
        return f"[[green]{datetime.now().strftime('%H:%M:%S')}[/]]"

    def pretty_cmd_str(self, command: list[str]) -> str:
        filter_git_log_args = VerbArgs.git_log.value[3:]
        return "chezmoi " + " ".join(
            [
                _
                for _ in command[1:]
                if _
                not in GlobalCmd.default_args.value
                + filter_git_log_args
                + [
                    VerbArgs.format_json.value,
                    VerbArgs.path_style_absolute.value,
                ]
            ]
        )

    def _log_command(self, command: list[str]) -> None:
        trimmed_cmd = self.pretty_cmd_str(command)
        time = self._log_time()
        color = theme.vars["primary-lighten-3"]
        log_line = f"{time} [{color}]{trimmed_cmd}[/]"
        self.write(log_line)

    def error(self, message: str) -> None:
        color = theme.vars["text-error"]
        time = self._log_time()
        self.write(f"{time} [{color}]{message}[/]")

    def warning(self, message: str) -> None:
        lines = message.splitlines()
        color = theme.vars["text-warning"]
        for line in [line for line in lines if line.strip()]:
            escaped_line = escape(line)
            self.write(f"{self._log_time()} [{color}]{escaped_line}[/]")

    def success(self, message: str) -> None:
        color = theme.vars["text-success"]
        self.write(f"{self._log_time()} [{color}]{message}[/]")

    def ready_to_run(self, message: str) -> None:
        color = theme.vars["accent-darken-3"]
        self.write(f"{self._log_time()} [{color}]{message}[/]")

    def dimmed(self, message: str) -> None:
        if message.strip() == "":
            return
        lines: list[str] = message.splitlines()
        color = theme.vars["text-disabled"]
        for line in lines:
            if line.strip():
                escaped_line = escape(line)
                self.write(f"[{color}]{escaped_line}[/]")


class AppLog(CommandLogBase):

    def __init__(self) -> None:
        super().__init__(
            id=LogsEnum.app_log.name,
            markup=True,
            max_lines=10000,
            classes=Tcss.log_views,
        )
        success = f"{Chars.check_mark} Success"
        self.succes_no_output = f"{success}, no output"
        self.success_with_output = f"{success}, output processed in UI"

    def completed_process(
        self, completed_process: CompletedProcess[str]
    ) -> None:
        self._log_command(completed_process.args)
        if completed_process.returncode == 0:
            if completed_process.stdout == "":
                self.success(self.succes_no_output)
            else:
                self.success(self.success_with_output)
        else:
            self.error(
                f"{Chars.x_mark} Command failed with exit code {completed_process.returncode}, stderr logged to Output log"
            )


class DebugLog(CommandLogBase):

    type Mro = tuple[type, ...]

    def __init__(self) -> None:
        super().__init__(
            id=LogsEnum.debug_log.name,
            markup=True,
            max_lines=10000,
            wrap=True,
            classes=Tcss.log_views,
        )

    def on_mount(self) -> None:
        self.add_class(Tcss.log_views)
        self.ready_to_run("Debug log ready to capture logs.")

    def mro(self, mro: Mro) -> None:
        color = theme.vars["accent-darken-2"]
        self.write(f"{self._log_time()} [{color}]Method Resolution Order:[/]")

        exclude = {
            "typing.Generic",
            "builtins.object",
            "textual.dom.DOMNode",
            "textual.message_pump.MessagePump",
            "chezmoi_mousse.id_typing.AppType",
        }

        pretty_mro = " -> ".join(
            f"{qname}\n"
            for cls in mro
            if not any(
                e in (qname := f"{cls.__module__}.{cls.__qualname__}")
                for e in exclude
            )
        )
        self.dimmed(pretty_mro)

    def list_attr(self, obj: object) -> None:
        members = [attr for attr in dir(obj) if not attr.startswith("_")]
        self.ready_to_run(f"{obj.__class__.__name__} attributes:")
        self.dimmed(", ".join(members))


class OutputLog(CommandLogBase):

    def __init__(self) -> None:
        super().__init__(
            id=LogsEnum.output_log.name, markup=True, max_lines=10000
        )

    def on_mount(self) -> None:
        self.add_class(Tcss.log_views)
        self.ready_to_run("Output log ready to capture logs.")

    def completed_process(
        self, completed_process: CompletedProcess[str]
    ) -> None:
        self._log_command(completed_process.args)
        if completed_process.returncode == 0:
            self.success("success, stdout:")
            if completed_process.stdout == "":
                self.dimmed("No output on stdout")
            else:
                self.dimmed(completed_process.stdout)
        else:
            self.error("failed, stderr:")
            self.dimmed(f"{completed_process.stderr}")
        self.refresh()


class Chezmoi:

    def __init__(self) -> None:
        self.app_log = AppLog()
        self.debug_log = DebugLog()
        self.output_log = OutputLog()

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

    def stripped_cmd(self, long_command: list[str]) -> str:
        return self.app_log.pretty_cmd_str(long_command)

    def _strip_stdout(self, stdout: str):
        # remove trailing and leading new lines but NOT leading whitespace
        stripped = stdout.lstrip("\n").rstrip()
        # remove intermediate empty lines
        return "\n".join(
            [line for line in stripped.splitlines() if line.strip()]
        )

    def _log_in_app_and_output_log(self, result: CompletedProcess[str]):
        result.stdout = self._strip_stdout(result.stdout)
        self.app_log.completed_process(result)
        self.output_log.completed_process(result)

    def read(self, read_cmd: ReadCmd, path: Path | None = None) -> str:
        command: list[str] = read_cmd.value
        if path is not None:
            command: list[str] = command + [str(path)]
        # CompletedProcess type arg is str as we use text=True
        result: CompletedProcess[str] = run(
            command, capture_output=True, shell=False, text=True, timeout=1
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
        self, tab_name: TabName, kind: Literal["dirs", "files"]
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
