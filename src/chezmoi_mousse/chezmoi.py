import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from shutil import which
from typing import Literal

from rich.markup import escape
from textual.widgets import RichLog

import chezmoi_mousse.custom_theme as theme
from chezmoi_mousse.constants import (
    Chars,
    IoVerbs,
    LogIdStr,
    OperateVerbs,
    ReadVerbs,
    TabName,
    TcssStr,
)
from chezmoi_mousse.id_typing import (
    CmdWords,
    Id,
    Mro,
    OperateHelp,
    ParsedJson,
    PathDict,
)

CHEZMOI_COMMAND_FOUND = which("chezmoi")

BASE_CMD = (
    "chezmoi",
    "--no-pager",
    "--color=off",
    "--no-tty",
    "--mode=file",
    "--progress=false",
    "--interactive=false",
    "--force",
)


class AllCommands(Enum):
    cat = BASE_CMD + (ReadVerbs.cat,)
    cat_config = BASE_CMD + (ReadVerbs.cat_config,)
    doctor = BASE_CMD + (IoVerbs.doctor,)
    diff = BASE_CMD + (ReadVerbs.diff,)
    dir_status_lines = BASE_CMD + (
        IoVerbs.status,
        "--path-style=absolute",
        "--include=dirs",
    )
    dump_config = BASE_CMD + (IoVerbs.dump_config, "--format=json")
    file_status_lines = BASE_CMD + (
        IoVerbs.status,
        "--path-style=absolute",
        "--include=files",
    )
    forget = BASE_CMD + (OperateVerbs.forget,)
    git_log = BASE_CMD + (
        ReadVerbs.git,
        "--",
        "log",
        "--max-count=50",
        "--no-color",
        "--no-decorate",
        "--date-order",
        "--no-expand-tabs",
        "--format=%ar by %cn;%s",
    )
    ignored = BASE_CMD + (ReadVerbs.ignored,)
    managed_dirs = BASE_CMD + (
        IoVerbs.managed,
        "--path-style=absolute",
        "--include=dirs",
    )
    managed_files = BASE_CMD + (
        IoVerbs.managed,
        "--path-style=absolute",
        "--include=files",
    )
    purge = BASE_CMD + (OperateVerbs.purge, "--force")
    source_path = BASE_CMD + (ReadVerbs.source_path,)
    template_data = BASE_CMD + (ReadVerbs.data, "--format=json")


class IoCmd(Enum):
    dir_status_lines = AllCommands.dir_status_lines.value
    doctor = AllCommands.doctor.value
    dump_config = AllCommands.dump_config.value
    file_status_lines = AllCommands.file_status_lines.value
    managed_dirs = AllCommands.managed_dirs.value
    managed_files = AllCommands.managed_files.value


class ReadCmd(Enum):
    cat = AllCommands.cat.value
    cat_config = AllCommands.cat_config.value
    diff = AllCommands.diff.value
    git_log = AllCommands.git_log.value
    ignored = AllCommands.ignored.value
    source_path = AllCommands.source_path.value
    template_data = AllCommands.template_data.value


class CommandLog(RichLog):
    def __init__(self, log_id: str) -> None:
        self.log_id = log_id
        super().__init__(
            id=self.log_id, auto_scroll=True, markup=True, max_lines=10000
        )

    def on_mount(self) -> None:
        if self.log_id == Id.init.log_id:
            self.border_title = " Init Log "
            self.add_class(TcssStr.operate_log)
        elif self.log_id == LogIdStr.operate_log:
            self.border_title = " Operate Log "
            self.add_class(TcssStr.operate_log)

    def _log_time(self) -> str:
        return f"[[green]{datetime.now().strftime('%H:%M:%S')}[/]]"

    def trimmed_cmd_str(self, command: CmdWords) -> str:
        return " ".join(
            [
                _
                for _ in command
                if _
                not in (
                    "--color=off"
                    "--date-order"
                    "--format=%ar by %cn;%s"
                    "--format=json"
                    "--mode=file"
                    "--no-color"
                    "--no-decorate"
                    "--no-expand-tabs"
                    "--no-pager"
                    "--no-tty"
                    "--path-style=absolute"
                    "--progress=false"
                    "--interactive=false"
                    "--force"
                )
            ]
        )

    def log_command(self, command: CmdWords) -> None:
        trimmed_cmd = self.trimmed_cmd_str(command)
        time = self._log_time()
        color = theme.vars["primary-lighten-3"]
        log_line = f"{time} [{color}]{trimmed_cmd}[/]"
        self.write(log_line)

    def log_error(self, message: str) -> None:
        color = theme.vars["text-error"]
        time = self._log_time()
        self.write(f"{time} [{color}]{message}[/]")

    def log_warning(self, message: str) -> None:
        lines = message.splitlines()
        color = theme.vars["text-warning"]
        for line in [line for line in lines if line.strip()]:
            escaped_line = escape(line)
            self.write(f"{self._log_time()} [{color}]{escaped_line}[/]")

    def log_success(self, message: str) -> None:
        color = theme.vars["text-success"]
        self.write(f"{self._log_time()} [{color}]{message}[/]")

    def log_ready_to_run(self, message: str) -> None:
        color = theme.vars["accent-darken-3"]
        self.write(f"{self._log_time()} [{color}]{message}[/]")

    def log_mro(self, mro: Mro) -> None:
        if os.environ.get("CHEZMOI_MOUSSE_DEV") != "1":
            return
        color = theme.vars["accent-darken-2"]
        self.write(f"{self._log_time()} [{color}]Method Resolution Order:[/]")
        pretty_mro = " -> ".join(
            f"{cls.__module__}.{cls.__qualname__}\n"
            for cls in mro
            if "typing.Generic" not in f"{cls.__module__}.{cls.__qualname__}"
            and "builtins.object" not in f"{cls.__module__}.{cls.__qualname__}"
        )
        self.log_dimmed(f"{pretty_mro}")

    def log_dimmed(self, message: str) -> None:
        if message.strip() == "":
            return
        lines: list[str] = message.splitlines()
        color = theme.vars["text-disabled"]
        for line in lines:
            if line.strip():
                escaped_line = escape(line)
                self.write(f"[{color}]{escaped_line}[/]")

    # used by the ContentsView class
    def log_read_path(self, message: str) -> None:
        color = theme.vars["primary-lighten-1"]
        self.write(f"{self._log_time()} [{color}]{message}[/]")


cmd_log = CommandLog(log_id=LogIdStr.app_log)
init_log = CommandLog(log_id=LogIdStr.init_log)
op_log = CommandLog(log_id=LogIdStr.operate_log)


if os.environ.get("CHEZMOI_MOUSSE_DEV") == "1":
    cmd_log.log_ready_to_run("Running in development mode")


def _run_cmd(long_command: CmdWords, time_out: float = 1) -> str:

    if not CHEZMOI_COMMAND_FOUND:
        return ""

    try:
        cmd_stdout = (
            subprocess.run(
                long_command,
                capture_output=True,
                check=True,  # raises exception for any non-zero return code
                shell=False,
                text=True,  # returns stdout as str instead of bytes
                timeout=5,  # maybe optimize for circumstances later on
            )
            .stdout.lstrip("\n")
            .rstrip()
        )
        cmd_log.log_command(long_command)
        if any(verb in long_command for verb in OperateVerbs):
            if (
                OperateVerbs.init in long_command
                or OperateVerbs.purge in long_command
            ):
                init_log.log_command(long_command)
            else:
                op_log.log_command(long_command)
            if cmd_stdout.strip() == "":
                msg = f"{Chars.check_mark} Command made changes successfully, no output"
                cmd_log.log_success(msg)
                if (
                    OperateVerbs.init in long_command
                    or OperateVerbs.purge in long_command
                ):
                    init_log.log_success(msg)
                else:
                    op_log.log_success(msg)
            else:
                msg = f"{Chars.check_mark} Command made changes successfully, output:"
                cmd_log.log_success(msg)
                cmd_log.log_dimmed(cmd_stdout)
                if (
                    OperateVerbs.init in long_command
                    or OperateVerbs.purge in long_command
                ):
                    init_log.log_success(msg)
                else:
                    op_log.log_success(msg)
                    op_log.log_dimmed(cmd_stdout)

            return cmd_stdout
        if any(verb in long_command for verb in IoVerbs):
            cmd_log.log_warning(
                "Subprocess call successful: InputOutput data updated"
            )
            return cmd_stdout
        elif any(verb in long_command for verb in ReadVerbs):
            cmd_log.log_warning("Subprocess call successful")
            return cmd_stdout
        else:
            cmd_log.log_success(
                "Subprocess call successful, no specific logging implemented"
            )
        return cmd_stdout
    except Exception as e:
        if "doctor" in long_command and isinstance(
            e, subprocess.CalledProcessError
        ):
            op_log.log_warning(
                f"{Chars.warning_sign} chezmoi doctor has a non-zero exit code"
            )
            return e.stdout.strip()
        if any(verb in long_command for verb in OperateVerbs):
            op_log.log_error(f"{Chars.x_mark} Command failed {e}")
        cmd_log.log_error(f"{Chars.x_mark} Command failed {e}")
        return "failed"


class ChangeCommand:
    """Group of commands which make changes on disk or in the chezmoi
    repository."""

    def __init__(self) -> None:
        self.base_cmd = BASE_CMD
        if os.environ.get("MOUSSE_ENABLE_CHANGES") != "1":
            self.base_cmd = BASE_CMD + ("--dry-run",)
            cmd_log.log_ready_to_run(OperateHelp.changes_mode_disabled.value)
        else:
            cmd_log.log_warning(OperateHelp.changes_mode_enabled.value)

    def _update_managed_status_data(self) -> None:
        # Update data that the managed_status property depends on
        chezmoi.managed_dirs.update()
        chezmoi.managed_files.update()
        chezmoi.dir_status_lines.update()
        chezmoi.file_status_lines.update()

    def add(self, path: Path) -> None:
        _run_cmd(self.base_cmd + (OperateVerbs.add, str(path)))
        self._update_managed_status_data()

    def add_encrypted(self, path: Path) -> None:
        _run_cmd(self.base_cmd + (OperateVerbs.add, "--encrypt", str(path)))
        self._update_managed_status_data()

    def re_add(self, path: Path) -> None:
        _run_cmd(self.base_cmd + (OperateVerbs.re_add, str(path)))
        self._update_managed_status_data()

    def apply(self, path: Path) -> None:
        _run_cmd(self.base_cmd + (OperateVerbs.apply, str(path)))
        self._update_managed_status_data()

    def destroy(self, path: Path) -> None:
        _run_cmd(self.base_cmd + (OperateVerbs.destroy, str(path)))
        self._update_managed_status_data()

    def forget(self, path: Path) -> None:
        _run_cmd(self.base_cmd + (OperateVerbs.forget, str(path)))
        self._update_managed_status_data()

    def init_clone_repo(self, repo_url: str) -> None:
        _run_cmd(self.base_cmd + (OperateVerbs.init, repo_url))

    def init_new_repo(self) -> None:
        _run_cmd(self.base_cmd + (OperateVerbs.init,))

    def purge(self) -> None:
        _run_cmd(self.base_cmd + (OperateVerbs.purge,))


class ReadCommand:
    """Group of commands that call subprocess.run() but do not store data in an
    InputOutput dataclass."""

    def apply_diff(self, file_path: Path) -> list[str]:
        long_command = ReadCmd.diff.value + (str(file_path),)
        return _run_cmd(long_command).splitlines()

    def add_diff(self, file_path: Path) -> list[str]:
        long_command = ReadCmd.diff.value + (str(file_path),)
        return _run_cmd(long_command).splitlines()

    def cat(self, file_path: Path) -> list[str]:
        return _run_cmd(ReadCmd.cat.value + (str(file_path),)).splitlines()

    def cat_config(self) -> list[str]:
        return [
            line
            for line in _run_cmd(ReadCmd.cat_config.value).splitlines()
            if line.strip()  # Filter out empty lines from config output
        ]

    def git_log(self, path: Path) -> list[str]:
        source_path: str = ""
        if not chezmoi_config.sourceDir:
            return []
        if path == chezmoi_config.destDir:
            source_path = str(chezmoi_config.sourceDir)
        else:
            source_path = _run_cmd(ReadCmd.source_path.value + (str(path),))
        long_command = ReadCmd.git_log.value + (source_path,)
        return _run_cmd(long_command).splitlines()

    def ignored(self) -> list[str]:
        return _run_cmd(ReadCmd.ignored.value).splitlines()

    def template_data(self) -> list[str]:
        return _run_cmd(ReadCmd.template_data.value).splitlines()

    def re_add_diff(self, file_path: Path) -> list[str]:
        long_command = ReadCmd.diff.value + (str(file_path), "--reverse")
        return _run_cmd(long_command).splitlines()


@dataclass
class ChezmoiConfig:
    autoadd: bool = False
    autocommit: bool = False
    autopush: bool = False
    destDir: Path = Path.home()
    sourceDir: Path | None = None

    def update_config_class(self, dump_config_stdout: str) -> None:
        parsed_config: ParsedJson = json.loads(dump_config_stdout)
        self.autoadd = parsed_config["git"]["autoadd"]
        self.autocommit = parsed_config["git"]["autocommit"]
        self.autopush = parsed_config["git"]["autopush"]
        self.destDir = Path(parsed_config["destDir"])
        self.sourceDir = Path(parsed_config["sourceDir"])


chezmoi_config = ChezmoiConfig()


@dataclass
class InputOutput:

    long_command: CmdWords
    arg_id: str
    # fields with defaults should go after non-default fields
    config_dump: ChezmoiConfig | None = None
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
        if IoVerbs.dump_config in self.long_command:
            chezmoi_config.update_config_class(self.std_out)


class Chezmoi:

    config_dump: InputOutput
    dir_status_lines: InputOutput
    doctor: InputOutput
    file_status_lines: InputOutput
    managed_dirs: InputOutput
    managed_files: InputOutput
    perform = ChangeCommand()
    run = ReadCommand()

    def __init__(self) -> None:

        self.long_commands: dict[str, CmdWords] = {}

        for long_cmd in IoCmd:
            self.long_commands[long_cmd.name] = long_cmd.value
            setattr(
                self,
                long_cmd.name,
                InputOutput(long_cmd.value, arg_id=long_cmd.name),
            )


chezmoi = Chezmoi()


class ManagedStatus:

    @property
    def dir_paths(self) -> list[Path]:
        return [Path(p) for p in chezmoi.managed_dirs.list_out]

    @property
    def file_paths(self) -> list[Path]:
        return [Path(p) for p in chezmoi.managed_files.list_out]

    def _create_status_dict(
        self, tab_name: TabName, kind: Literal["dirs", "files"]
    ) -> PathDict:
        path_dict: PathDict = {}
        status_idx: int = 0
        status_codes: str = ""
        if kind == "dirs":
            managed_paths = self.dir_paths
            status_lines = chezmoi.dir_status_lines.list_out
        elif kind == "files":
            managed_paths = self.file_paths
            status_lines = chezmoi.file_status_lines.list_out

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

    def managed_dirs_in(self, dir_path: Path) -> list[Path]:
        # checks only direct children
        return [p for p in self.dir_paths if p.parent == dir_path]

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


managed_status = ManagedStatus()
