import json
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from subprocess import run
from typing import Literal, NamedTuple

from rich.markup import escape
from textual.widgets import RichLog

from chezmoi_mousse import BASE_CMD, CM_CFG, theme
from chezmoi_mousse.id_typing import (
    ButtonEnum,
    CharsEnum,
    CmdWords,
    InputOutputVerbs,
    OperateIdStr,
    OperateVerbs,
    ParsedJson,
    ReadVerbs,
    StatusDict,
    TabStr,
    TcssStr,
)


@dataclass
class OperateData:
    path: Path = CM_CFG.destDir
    operation_executed: bool = False
    tab_name: TabStr | None = None
    found: bool | None = None
    button_name: ButtonEnum | None = None
    is_file: bool | None = None


class AllCommands(Enum):
    cat = BASE_CMD + (ReadVerbs.cat.value,)
    cat_config = BASE_CMD + (ReadVerbs.cat_config.value,)
    doctor = BASE_CMD + (InputOutputVerbs.doctor.value,)
    diff = BASE_CMD + (ReadVerbs.diff.value,)
    dir_status_lines = BASE_CMD + (
        InputOutputVerbs.status.value,
        "--path-style=absolute",
        "--include=dirs",
    )
    file_status_lines = BASE_CMD + (
        InputOutputVerbs.status.value,
        "--path-style=absolute",
        "--include=files",
    )
    forget = BASE_CMD + (OperateVerbs.forget.value,)
    git_log = BASE_CMD + (
        ReadVerbs.git.value,
        "--",
        "log",
        "--max-count=50",
        "--no-color",
        "--no-decorate",
        "--date-order",
        "--no-expand-tabs",
        "--format=%ar by %cn;%s",
    )
    ignored = BASE_CMD + (ReadVerbs.ignored.value,)
    managed_dirs = BASE_CMD + (
        InputOutputVerbs.managed.value,
        "--path-style=absolute",
        "--include=dirs",
    )
    managed_files = BASE_CMD + (
        InputOutputVerbs.managed.value,
        "--path-style=absolute",
        "--include=files",
    )
    source_path = BASE_CMD + (ReadVerbs.source_path.value,)
    template_data = BASE_CMD + (ReadVerbs.data.value, "--format=json")


class IoCmd(Enum):
    dir_status_lines = AllCommands.dir_status_lines.value
    doctor = AllCommands.doctor.value
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
    def __init__(self, id: str) -> None:
        super().__init__(id=id, auto_scroll=True, markup=True, max_lines=20000)

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
                    "--config"
                    "--date-order"
                    "--format=%ar by %cn;%s"
                    "--force"
                    "--format=json"
                    "--mode=file"
                    "--no-color"
                    "--no-decorate"
                    "--no-expand-tabs"
                    "--no-pager"
                    "--no-tty"
                    "--path-style=absolute"
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
        time = self._log_time()
        self.write(f"{time} [{color}]{message}[/]")


cmd_log = CommandLog(id=TabStr.log_tab)
op_log = CommandLog(id=OperateIdStr.operate_log_id)
op_log.add_class(TcssStr.op_log)


def subprocess_run(long_command: CmdWords, time_out: float = 1) -> str:
    check_mark = CharsEnum.check_mark.value
    x_mark = CharsEnum.x_mark.value

    try:
        cmd_stdout: str = run(
            long_command,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,
            text=True,  # returns stdout as str instead of bytes
            timeout=5,  # maybe optimize for circumstances later on
        ).stdout.strip()
        cmd_log.log_command(long_command)
        if any(verb.value in long_command for verb in OperateVerbs):
            op_log.log_command(long_command)
            if cmd_stdout.strip() == "":
                msg = f"{check_mark} Command made changes successfully, no output"
                op_log.log_success(msg)
                cmd_log.log_success(msg)
            else:
                msg = (
                    f"{check_mark} Command made changes successfully, output:"
                )
                op_log.log_success(msg)
                cmd_log.log_success(msg)
                op_log.log_dimmed(cmd_stdout)
                cmd_log.log_dimmed(cmd_stdout)
            return cmd_stdout
        if any(verb.value in long_command for verb in InputOutputVerbs):
            cmd_log.log_warning(
                "Subprocess call successful: InputOutput data updated"
            )
            return cmd_stdout
        elif any(verb.value in long_command for verb in ReadVerbs):
            cmd_log.log_warning("Subprocess call successful")
            return cmd_stdout
        else:
            cmd_log.log_success(
                "Subprocess call successful, no specific logging implemented"
            )
        return cmd_stdout
    except Exception as e:
        if any(verb.value in long_command for verb in OperateVerbs):
            op_log.log_error(f"{x_mark} Command failed {e}")
            cmd_log.log_error(f"{x_mark} Command failed {e}")
        return "failed"


class ChangeCommand:
    """Group of commands which make changes on disk or in the chezmoi
    repository."""

    config_path: Path | None = None

    def __init__(self, enable_changes: bool = False) -> None:
        if os.environ.get("MOUSSE_ENABLE_CHANGES") == "1":
            self.base = BASE_CMD + ("--force", "--config")
            cmd_log.log_warning(
                "Changes mode enabled, operations will be executed"
            )
        else:
            self.base = BASE_CMD + ("--dry-run", "--force", "--config")
            cmd_log.log_warning(
                "Changes mode disabled, operations will dry-run only"
            )

    def _update_managed_status_data(self) -> None:
        # Update data that the managed_status property depends on
        chezmoi.managed_dirs.update()
        chezmoi.managed_files.update()
        chezmoi.dir_status_lines.update()
        chezmoi.file_status_lines.update()

    def add(self, path: Path) -> None:
        subprocess_run(self.base + (str(self.config_path), "add", str(path)))
        self._update_managed_status_data()

    def re_add(self, path: Path) -> None:
        subprocess_run(
            self.base + (str(self.config_path), "re-add", str(path))
        )
        self._update_managed_status_data()

    def apply(self, path: Path) -> None:
        subprocess_run(self.base + (str(self.config_path), "apply", str(path)))
        self._update_managed_status_data()

    def forget(self, path: Path) -> None:
        subprocess_run(
            self.base + (str(self.config_path), "forget", str(path))
        )
        self._update_managed_status_data()

    def destroy(self, path: Path) -> None:
        subprocess_run(
            self.base + (str(self.config_path), "destroy", str(path))
        )
        self._update_managed_status_data()


class ReadCommand:
    """Group of commands that call subprocess.run() but do not store data in an
    InputOutput dataclass."""

    def apply_diff(self, file_path: Path) -> list[str]:
        long_command = ReadCmd.diff.value + (str(file_path),)
        return subprocess_run(long_command).splitlines()

    def cat(self, file_path: Path) -> list[str]:
        return subprocess_run(
            ReadCmd.cat.value + (str(file_path),)
        ).splitlines()

    def cat_config(self) -> list[str]:
        return [
            line
            for line in subprocess_run(ReadCmd.cat_config.value).splitlines()
            if line.strip()
        ]

    def git_log(self, path: Path) -> list[str]:
        source_path: str = ""
        if path == CM_CFG.destDir:
            source_path = str(CM_CFG.sourceDir)
        else:
            source_path = subprocess_run(
                ReadCmd.source_path.value + (str(path),)
            )
        long_command = ReadCmd.git_log.value + (source_path,)
        return subprocess_run(long_command).splitlines()

    def ignored(self) -> list[str]:
        return subprocess_run(ReadCmd.ignored.value).splitlines()

    def template_data(self) -> list[str]:
        return subprocess_run(ReadCmd.template_data.value).splitlines()

    def re_add_diff(self, file_path: Path) -> list[str]:
        long_command = ReadCmd.diff.value + (str(file_path), "--reverse")
        return subprocess_run(long_command).splitlines()


# named tuple nested in StatusPaths, to enable dot notation access
class StatusDicts(NamedTuple):
    dirs: StatusDict
    files: StatusDict

    @property
    def dirs_without_status(self) -> list[Path]:
        return [path for path, status in self.dirs.items() if status == "X"]

    @property
    def files_without_status(self) -> list[Path]:
        return [path for path, status in self.files.items() if status == "X"]

    @property
    def dirs_with_status(self) -> list[Path]:
        return [path for path, status in self.dirs.items() if status != "X"]

    @property
    def files_with_status(self) -> list[Path]:
        return [path for path, status in self.files.items() if status != "X"]


@dataclass
class InputOutput:

    long_command: CmdWords
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
        self.std_out = subprocess_run(self.long_command)


class Chezmoi:

    dir_status_lines: InputOutput
    doctor: InputOutput
    file_status_lines: InputOutput
    managed_dirs: InputOutput
    managed_files: InputOutput
    perform = ChangeCommand()
    run = ReadCommand()
    temp_config_path: Path

    def __init__(self) -> None:

        self.long_commands: dict[str, CmdWords] = {}

        for long_cmd in IoCmd:
            self.long_commands[long_cmd.name] = long_cmd.value
            setattr(
                self,
                long_cmd.name,
                InputOutput(long_cmd.value, arg_id=long_cmd.name),
            )

    @property
    def managed_dir_paths(self) -> list[Path]:
        return [Path(p) for p in self.managed_dirs.list_out]

    @property
    def managed_file_paths(self) -> list[Path]:
        return [Path(p) for p in self.managed_files.list_out]

    @property
    def managed_status(self) -> dict[str, StatusDicts]:
        """Returns a dict with keys "Apply" and "ReAdd", each mapping to a
        StatusDicts namedtuple containing a dirs and and files entry.

        These dicts maps output from chezmoi status as Path -> status_code.
        """

        def create_status_dict(
            tab_name: TabStr, kind: Literal["dirs", "files"]
        ) -> StatusDict:
            to_return: StatusDict = {}
            status_idx: int = 0
            status_codes: str = ""
            if kind == "dirs":
                managed_paths = self.managed_dir_paths
                status_lines = self.dir_status_lines.list_out
            elif kind == "files":
                managed_paths = self.managed_file_paths
                status_lines = self.file_status_lines.list_out

            if tab_name == TabStr.apply_tab:
                status_codes = "ADM"
                status_idx = 1
            elif tab_name == TabStr.re_add_tab:
                status_codes = "M"
                status_idx = 0

            paths_with_status_dict = {
                Path(line[3:]): line[status_idx]
                for line in status_lines
                if line[status_idx] in status_codes
            }

            for path in managed_paths:
                if path in paths_with_status_dict:
                    to_return[path] = paths_with_status_dict[path]
                else:
                    to_return[path] = "X"
            return to_return

        apply_dirs = create_status_dict(tab_name=TabStr.apply_tab, kind="dirs")
        apply_files = create_status_dict(
            tab_name=TabStr.apply_tab, kind="files"
        )
        re_add_dirs = create_status_dict(
            tab_name=TabStr.re_add_tab, kind="dirs"
        )
        re_add_files = create_status_dict(
            tab_name=TabStr.re_add_tab, kind="files"
        )

        return {
            TabStr.apply_tab: StatusDicts(dirs=apply_dirs, files=apply_files),
            TabStr.re_add_tab: StatusDicts(
                dirs=re_add_dirs, files=re_add_files
            ),
        }

    def managed_dirs_in(self, dir_path: Path) -> list[Path]:
        # checks only direct children

        return [p for p in self.managed_dir_paths if p.parent == dir_path]

    def files_with_status_in(
        self, tab_name: TabStr, dir_path: Path
    ) -> list[Path]:

        return [
            p
            for p in self.managed_status[tab_name].files_with_status
            if p.parent == dir_path
        ]

    def files_without_status_in(
        self, tab_name: TabStr, dir_path: Path
    ) -> list[Path]:

        return [
            p
            for p in self.managed_status[tab_name].files_without_status
            if p.parent == dir_path
        ]

    def dir_has_status_files(self, tab_name: TabStr, dir_path: Path) -> bool:
        # checks for any, no matter how deep in subdirectories

        return any(
            f
            for f, status in self.managed_status[tab_name].files.items()
            if dir_path in f.parents and status != "X"
        )

    def dir_has_status_dirs(self, tab_name: TabStr, dir_path: Path) -> bool:
        # checks for any, no matter how deep in subdirectories

        status_dirs = self.managed_status[tab_name].dirs.items()
        if dir_path.parent == CM_CFG.destDir and dir_path in status_dirs:
            # the parent is dest_dir, also return True because dest_dir is
            # not present in the self.managed_status dict
            return True
        return any(
            f
            for f, status in status_dirs
            if dir_path in f.parents and status != "X"
        )


chezmoi = Chezmoi()
