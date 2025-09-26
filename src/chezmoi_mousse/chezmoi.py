import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from shutil import which
from subprocess import CompletedProcess, run
from typing import Literal

from rich.markup import escape
from textual.widgets import RichLog

import chezmoi_mousse.custom_theme as theme
from chezmoi_mousse.constants import Chars, TabName, Tcss
from chezmoi_mousse.id_typing import OperateHelp, ParsedJson, PathDict

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
class InitConfig:
    changes_enabled: bool = os.environ.get("MOUSSE_ENABLE_CHANGES") == "1"
    chezmoi_cmd = CHEZMOI_CMD
    chezmoi_found: bool = which(CHEZMOI_CMD) is not None
    config_dump: ParsedJson | None = None
    destDir: Path = Path.home()
    dev_mode: bool = os.environ.get("CHEZMOI_MOUSSE_DEV") == "1"
    git_autoadd: bool = False
    git_autocommit: bool = False
    git_autopush: bool = False
    sourceDir: Path = Path(tempfile.gettempdir())

    def __post_init__(self):
        if os.environ.get("PRETEND_CHEZMOI_NOT_FOUND") == "1":
            self.chezmoi_found = False
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
            else:
                self.config_dump = {}


INIT_CFG = InitConfig()


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
            id=LogsEnum.app_log.name, markup=True, max_lines=10000
        )
        success = f"{Chars.check_mark} Success"
        self.succes_no_output = f"{success}, no output"
        self.success_with_output = f"{success}, output processed in UI"

    def on_mount(self) -> None:
        self.add_class(Tcss.log_views)
        if INIT_CFG.dev_mode:
            self.ready_to_run("Running in development mode")
        if not INIT_CFG.changes_enabled:
            self.ready_to_run(OperateHelp.changes_mode_disabled.value)
        else:
            self.warning(OperateHelp.changes_mode_enabled.value)

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
            id=LogsEnum.debug_log.name, markup=True, max_lines=10000
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


class InitLog(CommandLogBase):

    def __init__(self) -> None:
        super().__init__(
            id=LogsEnum.init_log.name, markup=True, max_lines=10000
        )

    def on_mount(self) -> None:
        self.add_class(Tcss.border_title_top, Tcss.bottom_docked_log)
        self.border_title = LogsEnum.init_log.value
        self.ready_to_run("Init log ready to capture logs.")


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


app_log = AppLog()
debug_log = DebugLog()
init_log = InitLog()
output_log = OutputLog()


class Chezmoi:

    def __init__(self) -> None:

        # Initialize managed_dirs and managed_files as empty strings
        self.managed_dirs = ""
        self.managed_files = ""
        self.dir_status_lines = ""
        self.file_status_lines = ""

    # PRE INIT CONFIG

    @property
    def init_cfg(self) -> InitConfig:
        return INIT_CFG

    @property
    def destDir(self) -> Path:
        return self.init_cfg.destDir

    @property
    def sourceDir(self) -> Path:
        return self.init_cfg.sourceDir

    # PRE INITIALIZED LOGS

    @property
    def app_log(self) -> AppLog:
        return app_log

    @property
    def debug_log(self) -> DebugLog:
        return debug_log

    @property
    def init_log(self) -> InitLog:
        return init_log

    @property
    def output_log(self) -> OutputLog:
        return output_log

    # COMMAND TYPES

    @property
    def _read_cmd(self) -> type[ReadCmd]:
        return ReadCmd

    @property
    def _change_cmd(self) -> type[ChangeCmd]:
        return ChangeCmd

    # CACHED CHEZMOI CMD OUTPUTS

    @property
    def dir_paths(self) -> list[Path]:
        return [Path(p) for p in self.managed_dirs.splitlines()]

    @property
    def file_paths(self) -> list[Path]:
        return [Path(p) for p in self.managed_files.splitlines()]

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

    def strip_stdout(self, stdout: str):
        # remove trailing and leading new lines but NOT leading whitespace
        stripped = stdout.lstrip("\n").rstrip()
        # remove intermediate empty lines
        return "\n".join(
            [line for line in stripped.splitlines() if line.strip()]
        )

    def log_in_app_and_output_log(self, result: CompletedProcess[str]):
        result.stdout = self.strip_stdout(result.stdout)
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
        self.log_in_app_and_output_log(result)
        return self.strip_stdout(result.stdout)

    def perform(
        self, change_sub_cmd: ChangeCmd, change_arg: str | None = None
    ) -> None:
        if self.init_cfg.changes_enabled:
            base_cmd: list[str] = GlobalCmd.live_run.value
        else:
            base_cmd: list[str] = GlobalCmd.dry_run.value
        command: list[str] = base_cmd + change_sub_cmd.value

        if change_arg is not None:
            command: list[str] = command + [change_arg]

        self.log_in_app_and_output_log(
            run(
                command, capture_output=True, shell=False, text=True, timeout=5
            )
        )

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
        return [p for p in self.dir_paths if p.parent == dir_path]

    def _create_status_dict(
        self, tab_name: TabName, kind: Literal["dirs", "files"]
    ) -> PathDict:
        path_dict: PathDict = {}
        status_idx: int = 0
        status_codes: str = ""
        if kind == "dirs":
            managed_paths = self.dir_paths
            status_lines = self.dir_status_lines.splitlines()
        elif kind == "files":
            managed_paths = self.file_paths
            status_lines = self.file_status_lines.splitlines()

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
