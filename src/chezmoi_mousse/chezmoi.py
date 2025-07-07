from enum import Enum
import json
import tempfile

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from subprocess import run
from typing import Any, Literal, NamedTuple

from textual.widgets import RichLog

from chezmoi_mousse import theme
from chezmoi_mousse.id_typing import (
    CharsEnum,
    CmdWords,
    PaneEnum,
    TabStr,
    OperateIdStr,
    TcssStr,
)


BASE = ("chezmoi", "--no-pager", "--color=off", "--no-tty", "--mode=file")


class InputOutputVerbs(Enum):
    # mapping of names to chezmoi verbs which store data in an InputOutput
    # dataclass

    cat_config = "cat-config"
    data = "data"
    doctor = "doctor"
    dump_config = "dump-config"
    ignored = "ignored"
    managed = "managed"
    status = "status"


class ReadVerbs(Enum):
    cat = "cat"
    diff = "diff"
    git = "git"
    source_path = "source-path"


class OperateVerbs(Enum):
    apply = "apply"
    re_add = "re-add"
    add = "add"


class AllCommands(Enum):
    cat = BASE + (ReadVerbs.cat.value,)
    cat_config = BASE + (InputOutputVerbs.cat_config.value,)
    doctor = BASE + (InputOutputVerbs.doctor.value,)
    dump_config = BASE + (InputOutputVerbs.dump_config.value, "--format=json")
    diff = BASE + (ReadVerbs.diff.value,)
    dir_status_lines = BASE + (
        InputOutputVerbs.status.value,
        "--path-style=absolute",
        "--include=dirs",
    )
    file_status_lines = BASE + (
        InputOutputVerbs.status.value,
        "--path-style=absolute",
        "--include=files",
    )
    git_log = BASE + (
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
    ignored = BASE + (InputOutputVerbs.ignored.value,)
    managed_dirs = BASE + (
        InputOutputVerbs.managed.value,
        "--path-style=absolute",
        "--include=dirs",
    )
    managed_files = BASE + (
        InputOutputVerbs.managed.value,
        "--path-style=absolute",
        "--include=files",
    )
    source_path = BASE + (ReadVerbs.source_path.value,)
    template_data = BASE + (InputOutputVerbs.data.value, "--format=json")


class IoCmd(Enum):
    cat_config = AllCommands.cat_config.value
    dir_status_lines = AllCommands.dir_status_lines.value
    doctor = AllCommands.doctor.value
    dump_config = AllCommands.dump_config.value
    file_status_lines = AllCommands.file_status_lines.value
    ignored = AllCommands.ignored.value
    managed_dirs = AllCommands.managed_dirs.value
    managed_files = AllCommands.managed_files.value
    template_data = AllCommands.template_data.value


class ReadCmd(Enum):
    cat = AllCommands.cat.value
    diff = AllCommands.diff.value
    git_log = AllCommands.git_log.value
    source_path = AllCommands.source_path.value


class CommandLog(RichLog):
    def __init__(self, id: str, classes: str = "") -> None:
        super().__init__(
            id=id,
            auto_scroll=True,
            markup=True,
            max_lines=20000,
            classes=classes,
        )

    def _log_time(self) -> str:
        return f"[green]{datetime.now().strftime('%H:%M:%S')}[/]"

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

    def log_command(self, command: CmdWords) -> str:
        trimmed_cmd = self.trimmed_cmd_str(command)
        log_time = f"[{self._log_time()}]"
        log_line = (
            f"{log_time} [{theme.vars["primary-lighten-3"]}]{trimmed_cmd}[/]"
        )
        self.write(log_line)
        return log_line  # used by the log in the Operate modalscreen

    def log_error(self, message: str) -> None:
        self.write(
            f"[{self._log_time()}] [{theme.vars["text-error"]}]{message}[/]"
        )

    def log_output(self, message: str) -> None:
        self.write(
            f"[{self._log_time()}] [{theme.vars["text-warning"]}]{message}[/]"
        )

    def log_app_msg(self, message: str) -> None:
        self.write(
            f"[{self._log_time()}] [{theme.vars["text-success"]}]{message}[/]"
        )

    def log_exception(self, message: str) -> None:
        self.write(f"{theme.vars["text-disabled"]}]{message}[/]")

    def log_read_file(self, file_path: Path) -> None:
        # If a file is not read with chezmoi cat but directly from disk,
        # also log a command with the same style. Used in ContentsView.
        self.write(
            f"[{self._log_time()}] [{theme.vars["primary-lighten-3"]}]"
            f"Reading file: {file_path}[/]"
        )


cmd_log = CommandLog(id=PaneEnum.log.value)
op_log = CommandLog(id=OperateIdStr.operate_log_id, classes=TcssStr.op_log)


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
            timeout=1,
        ).stdout.strip()
        cmd_log.log_command(long_command)
        if any(verb.value in long_command for verb in OperateVerbs):
            op_log.log_command(long_command)
        if any(verb.value in long_command for verb in InputOutputVerbs):
            cmd_log.log_output("InputOutput command successful")
            return cmd_stdout
        elif any(verb.value in long_command for verb in ReadVerbs):
            cmd_log.log_output("Read command successful")
            return cmd_stdout
        elif any(verb.value in long_command for verb in OperateVerbs):
            message = (
                f"{check_mark} command successful, subprocess exit code 0"
            )
            cmd_log.log_app_msg(message)
            op_log.log_app_msg(message)
            op_log.log_output(f"{cmd_stdout}")
        else:
            cmd_log.log_app_msg("command successful, no specific logging")
        return cmd_stdout
    except Exception as e:
        if any(verb.value in long_command for verb in OperateVerbs):
            op_log.log_error(f"{x_mark} command failed")
        else:
            cmd_log.log_error("command failed")
        cmd_log.log_exception(f"{e}")
        return "failed"


class ChangeCommand:
    """Group of commands which make changes on disk or in the chezmoi
    repository."""

    # TODO: remove --dry-run
    base = BASE + ("--dry-run", "--force", "--config")
    config_path: Path | None = None

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


class ReadCommand:
    """Group of commands that call subprocess.run() but do not store data in an
    InputOutput dataclass."""

    def apply_diff(self, file_path: Path) -> list[str]:
        long_command = ReadCmd.diff.value + (str(file_path),)
        return subprocess_run(long_command).splitlines()

    def cat(self, file_path: Path) -> str:
        return subprocess_run(ReadCmd.cat.value + (str(file_path),))

    def git_log(self, path: Path) -> list[str]:
        source_path: str = ""
        if path == chezmoi.dest_dir:
            source_path = str(chezmoi.source_dir)
        else:
            source_path = subprocess_run(
                ReadCmd.source_path.value + (str(path),)
            )
        long_command = ReadCmd.git_log.value + (source_path,)
        return subprocess_run(long_command).splitlines()

    def re_add_diff(self, file_path: Path) -> list[str]:
        long_command = ReadCmd.diff.value + (str(file_path), "--reverse")
        return subprocess_run(long_command).splitlines()


# named tuple nested in StatusPaths, to enable dot notation access
class StatusDicts(NamedTuple):
    dirs: dict[Path, str]
    files: dict[Path, str]

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
    dict_out: dict[str, Any] = field(default_factory=dict[str, Any])
    list_out: list[str] = field(default_factory=list[str])

    @property
    def label(self):
        return f'chezmoi {self.arg_id.replace("_", " ")}'

    def update(self) -> None:
        self.std_out = subprocess_run(self.long_command)
        self.list_out = self.std_out.splitlines()
        try:
            result: Any = json.loads(self.std_out)
            if isinstance(result, dict):
                self.dict_out: dict[str, Any] = result
            else:
                self.dict_out = {}

        except (json.JSONDecodeError, ValueError):
            self.dict_out = {}


class Chezmoi:

    cat_config: InputOutput
    dir_status_lines: InputOutput
    doctor: InputOutput
    dump_config: InputOutput
    file_status_lines: InputOutput
    ignored: InputOutput
    managed_dirs: InputOutput
    managed_files: InputOutput
    perform = ChangeCommand()
    template_data: InputOutput
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
    def source_dir(self) -> Path:
        return Path(self.dump_config.dict_out["sourceDir"])

    @property
    def dest_dir(self) -> Path:
        return Path(self.dump_config.dict_out["destDir"])

    @property
    def dest_dir_str(self) -> str:
        return self.dump_config.dict_out["destDir"]

    @property
    def autoadd_enabled(self) -> bool:
        return self.dump_config.dict_out["git"]["autoadd"]

    @property
    def autocommit_enabled(self) -> bool:
        return self.dump_config.dict_out["git"]["autocommit"]

    @property
    def autopush_enabled(self) -> bool:
        return self.dump_config.dict_out["git"]["autopush"]

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
            tab_name: str, kind: Literal["dirs", "files"]
        ) -> dict[Path, str]:
            to_return: dict[Path, str] = {}
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

    def _validate_managed_dir_path(self, dir_path: Path) -> None:
        if (
            dir_path != self.dest_dir
            and dir_path not in self.managed_dir_paths
        ):
            raise ValueError(
                f"{dir_path} is not {self.dest_dir} or a managed directory."
            )

    def managed_dirs_in(self, dir_path: Path) -> list[Path]:
        # checks only direct children
        self._validate_managed_dir_path(dir_path)
        return [p for p in self.managed_dir_paths if p.parent == dir_path]

    def managed_files_in(self, dir_path: Path) -> list[Path]:
        # checks only direct children
        self._validate_managed_dir_path(dir_path)
        return [p for p in self.managed_file_paths if p.parent == dir_path]

    def dirs_with_status_in(
        # checks only direct children
        self,
        tab_str: TabStr,
        dir_path: Path,
    ) -> list[Path]:
        self._validate_managed_dir_path(dir_path)
        return [
            p
            for p in self.managed_status[tab_str].dirs_with_status
            if p.parent == dir_path
        ]

    def files_with_status_in(
        self, tab_str: TabStr, dir_path: Path
    ) -> list[Path]:
        self._validate_managed_dir_path(dir_path)
        return [
            p
            for p in self.managed_status[tab_str].files_with_status
            if p.parent == dir_path
        ]

    def dirs_without_status_in(
        self, tab_str: TabStr, dir_path: Path
    ) -> list[Path]:
        self._validate_managed_dir_path(dir_path)
        return [
            p
            for p in self.managed_status[tab_str].dirs_without_status
            if p.parent == dir_path
        ]

    def files_without_status_in(
        self, tab_str: TabStr, dir_path: Path
    ) -> list[Path]:
        self._validate_managed_dir_path(dir_path)
        return [
            p
            for p in self.managed_status[tab_str].files_without_status
            if p.parent == dir_path
        ]

    def dir_has_managed_files(self, dir_path: Path) -> bool:
        # checks for any, no matter how deep in subdirectories
        self._validate_managed_dir_path(dir_path)
        return any(f for f in self.managed_file_paths if dir_path in f.parents)

    def dir_has_status_files(self, tab_str: TabStr, dir_path: Path) -> bool:
        # checks for any, no matter how deep in subdirectories
        self._validate_managed_dir_path(dir_path)
        return any(
            f
            for f, status in self.managed_status[tab_str].files.items()
            if dir_path in f.parents and status != "X"
        )

    def dir_has_status_dirs(self, tab_str: TabStr, dir_path: Path) -> bool:
        # checks for any, no matter how deep in subdirectories
        self._validate_managed_dir_path(dir_path)
        status_dirs = self.managed_status[tab_str].dirs.items()
        if dir_path.parent == self.dest_dir and dir_path in status_dirs:
            # the parent is dest_dir, also return True because dest_dir is
            # not present in the self.managed_status dict
            return True
        return any(
            f
            for f, status in status_dirs
            if dir_path in f.parents and status != "X"
        )

    def check_interactive(self) -> bool:
        for line in self.cat_config.list_out:
            if "interactive" in line.lower() and "true" in line.lower():
                return True
        return False

    def create_temp_config_file(self) -> Path:
        # create temporary config file without interactive option, returns the
        # path to this file, or None if no config file is found
        config_file_name: str | None = None
        for line in chezmoi.doctor.list_out:
            if "config-file" in line and "found" in line:
                # Example line: "ok config-file found ~/.config/chezmoi/chezmoi.toml, last modified ..."
                parts = line.split("found ")
                if len(parts) > 1:
                    config_file_name = Path(
                        parts[1].split(",")[0].strip()
                    ).name
                    break

        if config_file_name is None:
            raise RuntimeError(
                "No config file found in chezmoi doctor output."
            )

        # read and create config
        config_text = self.cat_config.std_out
        filtered_lines: list[str] = [
            line
            for line in config_text.splitlines()
            if not line.lower().startswith("interactive")
        ]

        # write to new temp file
        temp_file_path: Path = Path(tempfile.gettempdir()) / config_file_name
        with open(temp_file_path, "w") as temp_file:
            temp_file.write("\n".join(filtered_lines))

        return temp_file_path


chezmoi = Chezmoi()
