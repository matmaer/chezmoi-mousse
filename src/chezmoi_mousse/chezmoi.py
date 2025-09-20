import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, StrEnum, auto
from pathlib import Path
from shutil import which
from types import SimpleNamespace
from typing import Literal

from rich.markup import escape
from textual.widgets import RichLog

import chezmoi_mousse.custom_theme as theme
from chezmoi_mousse.constants import (
    BorderTitle,
    Chars,
    IoVerbs,
    OperateVerbs,
    ReadVerbs,
    TabName,
    TcssStr,
    ViewName,
)
from chezmoi_mousse.id_typing import (
    Id,
    Mro,
    OperateHelp,
    ParsedJson,
    PathDict,
    TabIds,
)


@dataclass
class AppConfig:
    """Configuration for the chezmoi-mousse application."""

    name: str = "chezmoi"
    which_chezmoi: str | None = None
    dev_mode: bool = False
    changes_enabled: bool = False

    def __post_init__(self):
        self.dev_mode = os.environ.get("CHEZMOI_MOUSSE_DEV") == "1"
        self.changes_enabled = os.environ.get("MOUSSE_ENABLE_CHANGES") == "1"
        self.pretend_chezmoi_not_found = (
            os.environ.get("PRETEND_CHEZMOI_NOT_FOUND") == "1"
        )
        self.which_chezmoi = which(self.name)

    @property
    def chezmoi_found(self) -> bool:
        return (
            True
            if self.which_chezmoi and not self.pretend_chezmoi_not_found
            else False
        )

    @property
    def exe(self) -> str:
        return self.which_chezmoi or "exit"


APP_CFG = AppConfig()


########################
# Create Log instances #
########################


class LogIds(StrEnum):
    init_log = auto()
    operate_log = auto()


class CommandLog(RichLog):
    def __init__(
        self, *, ids: TabIds | LogIds, view_name: ViewName | None = None
    ) -> None:
        self.ids = ids
        self.view_name = view_name
        if self.view_name is not None and isinstance(self.ids, TabIds):
            self.rich_log_id = self.ids.view_id(view=self.view_name)
        elif isinstance(self.ids, LogIds):
            self.rich_log_id = self.ids.value
        super().__init__(
            id=self.rich_log_id,
            auto_scroll=True,
            markup=True,
            max_lines=10000,
            wrap=True,
        )

    def on_mount(self) -> None:
        if self.id == LogIds.init_log:
            self.add_class(TcssStr.border_title_top)
            self.border_title = BorderTitle.init_log
            self.add_class(TcssStr.bottom_docked_log)
        elif self.id == LogIds.operate_log:
            self.add_class(TcssStr.border_title_top)
            self.border_title = BorderTitle.operante_log
            self.add_class(TcssStr.bottom_docked_log)
        elif self.ids == Id.logs:
            self.add_class(TcssStr.log_views)
            if self.view_name == ViewName.app_log_view and APP_CFG.dev_mode:
                app_log.ready_to_run("Running in development mode")
            elif self.view_name == ViewName.debug_log_view:
                self.ready_to_run("Debug log ready to capture logs.")

    def _log_time(self) -> str:
        return f"[[green]{datetime.now().strftime('%H:%M:%S')}[/]]"

    def _pretty_cmd_str(self, command: list[str]) -> str:
        filter_git_log_args = VerbArgs.git_log.value[3:]
        return f"{APP_CFG.name} " + " ".join(
            [
                _
                for _ in command[1:]
                if _
                not in Cmd.default_args.value
                + filter_git_log_args
                + [
                    VerbArgs.format_json.value,
                    VerbArgs.path_style_absolute.value,
                ]
            ]
        )

    def command(self, command: list[str]) -> None:
        trimmed_cmd = self._pretty_cmd_str(command)
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


class DebugLog(CommandLog):

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


app_log = CommandLog(ids=Id.logs, view_name=ViewName.app_log_view)
debug_log = DebugLog(ids=Id.logs, view_name=ViewName.debug_log_view)
init_log = CommandLog(ids=LogIds.init_log)
op_log = CommandLog(ids=LogIds.operate_log)
# TODO: implement output log as a list of collapsibles
output_log = CommandLog(ids=Id.logs, view_name=ViewName.output_log_view)


#######################
# Define Enum classes #
#######################


class Cmd(Enum):
    chezmoi = [APP_CFG.exe]
    default_args = [
        "--color=off",
        "--force",
        "--interactive=false",
        "--mode=file",
        "--no-pager",
        "--no-tty",
        "--progress=false",
    ]
    default = chezmoi + default_args
    dry_run = default + ["--dry-run"]


class VerbArgs(Enum):
    format_json = "--format=json"
    include_dirs = "--include=dirs"
    include_files = "--include=files"
    path_style_absolute = "--path-style=absolute"
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


class IoCmd(Enum):
    doctor = Cmd.default.value + [IoVerbs.doctor]
    dir_status_lines = Cmd.default.value + [
        IoVerbs.status,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_dirs.value,
    ]
    file_status_lines = Cmd.default.value + [
        IoVerbs.status,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_files.value,
    ]
    managed_dirs = Cmd.default.value + [
        IoVerbs.managed,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_dirs.value,
    ]
    managed_files = Cmd.default.value + [
        IoVerbs.managed,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_files.value,
    ]


def _run_cmd(long_command: list[str]) -> str:
    if not APP_CFG.chezmoi_found:
        return ""
    # if a command contains failed, earlier on another command failed
    elif "failed" in long_command:
        return ""

    # TODO: implement spinner for commands taking a bit longer like operations
    # TODO: set different timeout values depending on nature of command
    # TODO: implement 'chezmoi verify', if exit 0, display message in Tree
    # widgets inform the user why the Tree widget is empty

    try:
        cmd_stdout = (
            subprocess.run(
                long_command,
                capture_output=True,
                check=True,  # raises exception for any non-zero return code
                shell=False,
                text=True,  # returns stdout as str instead of bytes
                timeout=5,
            )
            .stdout.lstrip("\n")
            .rstrip()
        )
        app_log.command(long_command)
        output_log.command(long_command)
        # log all commands stdout to output_log
        if cmd_stdout.strip() == "":
            output_log.dimmed("Command returned no output on stdout")
        else:
            output_log.dimmed(cmd_stdout)
        # handle operate logging
        if any(verb in long_command for verb in OperateVerbs):
            if (
                OperateVerbs.init in long_command
                or OperateVerbs.purge in long_command
            ):
                init_log.command(long_command)
            else:
                op_log.command(long_command)
            if cmd_stdout.strip() == "":
                msg = f"{Chars.check_mark} Command made changes successfully, no output"
                app_log.success(msg)
                if (
                    OperateVerbs.init in long_command
                    or OperateVerbs.purge in long_command
                ):
                    init_log.success(msg)
                else:
                    op_log.success(msg)
            else:
                app_log.success(
                    f"{Chars.check_mark} Exit status 0, stdout logged to output log"
                )
                msg = f"{Chars.check_mark} Command ran successfully, exit status 0"
                if (
                    OperateVerbs.init in long_command
                    or OperateVerbs.purge in long_command
                ):
                    init_log.success(msg)
                    init_log.dimmed(cmd_stdout)
                else:
                    op_log.success(msg)
                    op_log.dimmed(cmd_stdout)

            return cmd_stdout
        # handle IoVerb logging
        if long_command in IoCmd:
            app_log.warning(
                "InputOutput data updated for processing in the app"
            )
            return cmd_stdout
        elif any(verb in long_command for verb in ReadVerbs):
            app_log.warning("Data available to display in the app")
            return cmd_stdout
        else:
            app_log.error("No specific logging implemented")
        return cmd_stdout
    except Exception as e:

        # log to output_log
        output_log.command(long_command)
        attribs = [
            a
            for a in dir(e)
            if not a.startswith("_")
            and a not in ["add_note", "with_traceback"]
        ]
        dimmed_msg = ""
        output_log.error("An error occurred, exception data:")
        for attr in attribs:
            dimmed_msg += f"{attr}:\n{getattr(e, attr)}\n"
        output_log.dimmed(dimmed_msg)

        # log to app_log, op_log, init_log
        cmd_failed_msg = f"{Chars.x_mark} Command failed, exception logged to Output log, see Logs tab"

        # log to app_log
        app_log.command(long_command)
        app_log.error(cmd_failed_msg)

        # log to op_log or init_log
        if any(verb in long_command for verb in OperateVerbs):
            if "init" in long_command:
                init_log.command(long_command)
                init_log.error(cmd_failed_msg)
                return "failed"
            op_log.command(long_command)
            op_log.error(cmd_failed_msg)
        return "failed"


class ChangeCommand:
    """Group of commands which make changes on disk or in the chezmoi
    repository."""

    def __init__(self) -> None:
        self.base_cmd: list[str] = Cmd.default.value
        if not APP_CFG.changes_enabled:
            self.base_cmd = Cmd.dry_run.value
            app_log.ready_to_run(OperateHelp.changes_mode_disabled.value)
        else:
            app_log.warning(OperateHelp.changes_mode_enabled.value)

    def add(self, path: Path) -> None:
        _run_cmd(self.base_cmd + [OperateVerbs.add, str(path)])

    def add_encrypted(self, path: Path) -> None:
        _run_cmd(self.base_cmd + [OperateVerbs.add, "--encrypt", str(path)])

    def re_add(self, path: Path) -> None:
        _run_cmd(self.base_cmd + [OperateVerbs.re_add, str(path)])

    def apply(self, path: Path) -> None:
        _run_cmd(self.base_cmd + [OperateVerbs.apply, str(path)])

    def destroy(self, path: Path) -> None:
        _run_cmd(self.base_cmd + [OperateVerbs.destroy, str(path)])

    def forget(self, path: Path) -> None:
        _run_cmd(self.base_cmd + [OperateVerbs.forget, str(path)])

    def init_clone_repo(self, repo_url: str) -> None:
        _run_cmd(self.base_cmd + [OperateVerbs.init, repo_url])

    def init_new_repo(self) -> None:
        _run_cmd(self.base_cmd + [OperateVerbs.init])

    def purge(self) -> None:
        _run_cmd(self.base_cmd + [OperateVerbs.purge])


class ReadCommand:

    def __init__(self, *, dest_dir: Path, source_dir: Path):
        self.dest_dir = dest_dir
        self.source_dir = source_dir

    @staticmethod  # called in Chezmoi __init__
    def dump_config():
        command = Cmd.default.value + [
            VerbArgs.format_json.value,
            IoVerbs.dump_config,
        ]
        return _run_cmd(command)

    def cat(self, file_path: Path) -> list[str]:
        return _run_cmd(
            Cmd.default.value + [ReadVerbs.cat] + [str(file_path)]
        ).splitlines()

    def cat_config(self) -> list[str]:
        return [
            line
            for line in _run_cmd(
                Cmd.default.value + [ReadVerbs.cat_config]
            ).splitlines()
            if line.strip()  # Filter out empty lines from config output
        ]

    def diff(self, file_path: Path) -> list[str]:
        return _run_cmd(
            Cmd.default.value + [ReadVerbs.diff] + [str(file_path)]
        ).splitlines()

    def diff_reversed(self, file_path: Path) -> list[str]:
        return _run_cmd(
            Cmd.default.value
            + [ReadVerbs.diff]
            + [str(file_path), "--reverse"]
        ).splitlines()

    def git_log(self, path: Path) -> list[str]:
        source_path = self.source_path(path)
        command = (
            Cmd.default.value
            + [ReadVerbs.git]
            + VerbArgs.git_log.value
            + [str(source_path)]
        )
        return _run_cmd(command).splitlines()

    def ignored(self) -> list[str]:
        return _run_cmd(Cmd.default.value + [ReadVerbs.ignored]).splitlines()

    def source_path(self, path: Path) -> Path:
        if path == self.dest_dir:
            return self.source_dir
        return Path(
            _run_cmd(Cmd.default.value + [ReadVerbs.source_path] + [str(path)])
        )

    def template_data(self) -> list[str]:
        return _run_cmd(Cmd.default.value + [ReadVerbs.data]).splitlines()


@dataclass
class InputOutput:

    long_command: list[str]
    arg_id: str
    std_out: str = ""

    @property
    def label(self):
        return f'chezmoi {self.arg_id.replace("_", " ")}'

    @property
    def list_out(self):
        return self.std_out.splitlines()

    @property
    def dict_out(self) -> ParsedJson:
        try:
            result: ParsedJson = json.loads(self.std_out)
            return result
        except (json.JSONDecodeError, ValueError):
            return {}

    def update(self) -> None:
        self.std_out = _run_cmd(self.long_command)


class Chezmoi:

    _names = SimpleNamespace()
    dir_status_lines: InputOutput
    doctor: InputOutput
    file_status_lines: InputOutput
    managed_dirs: InputOutput
    managed_files: InputOutput
    perform = ChangeCommand()

    def __init__(self) -> None:
        self.destDir = Path()
        self.sourceDir = Path()
        if not APP_CFG.chezmoi_found:
            self.run = ReadCommand(
                dest_dir=self.destDir, source_dir=self.sourceDir
            )
        else:
            self.config_dump: ParsedJson = json.loads(
                ReadCommand.dump_config()
            )
            self.destDir: Path = Path(self.config_dump["destDir"])
            self.sourceDir: Path = Path(self.config_dump["sourceDir"])
            self.run = ReadCommand(
                dest_dir=self.destDir, source_dir=self.sourceDir
            )

        self.io_commands: dict[str, list[str]] = {}
        io_cmds: list[IoCmd] = [
            IoCmd.dir_status_lines,
            IoCmd.doctor,
            IoCmd.file_status_lines,
            IoCmd.managed_dirs,
            IoCmd.managed_files,
        ]
        for long_cmd in io_cmds:
            self.io_commands[long_cmd.name] = long_cmd.value
            setattr(
                self,
                long_cmd.name,
                InputOutput(long_cmd.value, arg_id=long_cmd.name),
            )

    @property
    def app_cfg(self):
        return APP_CFG

    @property
    def config(self):
        self._names.autoadd = self.config_dump["git"]["autoadd"]
        self._names.autocommit = self.config_dump["git"]["autocommit"]
        self._names.autopush = self.config_dump["git"]["autopush"]
        return self._names

    @property
    def app_log(self):
        return app_log

    @property
    def debug_log(self):
        return debug_log

    @property
    def init_log(self):
        return init_log

    @property
    def op_log(self):
        return op_log

    @property
    def output_log(self):
        return output_log

    @property
    def dir_paths(self) -> list[Path]:
        return [Path(p) for p in self.managed_dirs.list_out]

    @property
    def file_paths(self) -> list[Path]:
        return [Path(p) for p in self.managed_files.list_out]

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

    def update_managed_status_data(self) -> None:
        # Update data that the managed_status property depends on
        # TODO: do not run when operation is cancelled and properly update
        # Tree widgets after a relevant operation
        # DirectoryTree refreshes correctly
        self.managed_dirs.update()
        self.managed_files.update()
        self.dir_status_lines.update()
        self.file_status_lines.update()

    def _create_status_dict(
        self, tab_name: TabName, kind: Literal["dirs", "files"]
    ) -> PathDict:
        path_dict: PathDict = {}
        status_idx: int = 0
        status_codes: str = ""
        if kind == "dirs":
            managed_paths = self.dir_paths
            status_lines = self.dir_status_lines.list_out
        elif kind == "files":
            managed_paths = self.file_paths
            status_lines = self.file_status_lines.list_out

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
