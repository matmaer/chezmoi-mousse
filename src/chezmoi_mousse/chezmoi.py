import json
import tempfile

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from subprocess import TimeoutExpired, run
from typing import Any, Literal, NamedTuple

from textual.widgets import RichLog

from chezmoi_mousse import theme
from chezmoi_mousse.id_typing import (
    CharsEnum,
    PaneEnum,
    TabStr,
    OperateIdStr,
    TcssStr,
)

BASE = ("chezmoi", "--no-pager", "--color=off", "--no-tty", "--mode=file")

# https://www.chezmoi.io/reference/command-line-flags/common/#available-entry-types
SUBS: dict[str, tuple[str, ...]] = {
    "cat_config": ("cat-config",),
    "doctor": ("doctor",),
    "dump_config": ("dump-config", "--format=json"),
    "git_log": (
        "git",
        "--",
        "log",
        "--max-count=100",
        "--no-color",
        "--no-decorate",
        "--date-order",
        "--no-expand-tabs",
        "--format=%ar by %cn;%s",
    ),
    "ignored": ("ignored",),
    "managed_dirs": ("managed", "--path-style=absolute", "--include=dirs"),
    "managed_files": ("managed", "--path-style=absolute", "--include=files"),
    "dir_status_lines": ("status", "--path-style=absolute", "--include=dirs"),
    "file_status_lines": (
        "status",
        "--path-style=absolute",
        "--include=files",
    ),
    "template_data": ("data", "--format=json"),
}


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

    def trimmed_cmd_str(self, command: tuple[str, ...]) -> str:
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

    def log_command(self, command: tuple[str, ...]) -> str:
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


cmd_log = CommandLog(id=PaneEnum.log.value)
op_log = CommandLog(id=OperateIdStr.operate_log_id, classes=TcssStr.op_log)


def subprocess_run(long_command: tuple[str, ...]) -> str:
    check_mark = CharsEnum.check_mark.value

    try:
        cmd_log.log_command(long_command)
        if any(verb in long_command for verb in ("apply", "re-add", "add")):
            op_log.log_command(long_command)
        cmd_stdout: str = run(
            long_command,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,
            text=True,  # returns stdout as str instead of bytes
            timeout=1,
        ).stdout.strip()
        # treat commands from LiveCommands
        if "source-path" in long_command:
            cmd_log.log_app_msg("source-path returned for next command")
        elif "diff" in long_command:
            cmd_log.log_output("diff lines ready to render in gui")
        elif "cat" in long_command:
            cmd_log.log_output("file contents ready to render in gui")
        elif "git" in long_command and "log" in long_command:
            cmd_log.log_output("git log table ready to render in gui")
        elif "managed" in long_command:
            cmd_log.log_output(
                "managed paths updated in InputOutput dataclass"
            )
        elif "status" in long_command:
            cmd_log.log_output("status output ready to render in gui")
        elif "apply" in long_command:
            cmd_log.log_app_msg(f"{check_mark} apply command successful")
            op_log.log_app_msg(f"{check_mark} apply command successful")
        elif "re-add" in long_command:
            cmd_log.log_app_msg(f"{check_mark} re-add command successful")
            op_log.log_app_msg(f"{check_mark} re-add command successful")
        elif "add" in long_command:
            cmd_log.log_app_msg(f"{check_mark} add command successful")
            op_log.log_app_msg(f"{check_mark} add command successful")
        else:
            cmd_log.log_app_msg(
                "command successful, but no specific logging for it"
            )
        return cmd_stdout
    except TimeoutExpired:
        cmd_log.log_error("command timed out after 1 second")
        return "failed"
    except Exception as e:
        cmd_log.log_error(f"command failed: {e}")
        return "failed"


class PerformChange:
    """Group of commands which make changes on disk or in the chezmoi
    repository, does not store data in an InputOutput dataclass."""

    # TODO: remove --dry-run
    base = BASE + ("--dry-run", "--force", "--config")
    config_path: Path | None = None

    def _update_managed_status_data(self) -> None:
        # Update data that the managed_status property depends on
        chezmoi.managed_dirs.update()
        chezmoi.managed_files.update()
        chezmoi.dir_status_lines.update()
        chezmoi.file_status_lines.update()
        cmd_log.log_app_msg("new data stored InputOutput dataclass")

    def add(self, path: Path) -> None:
        command = self.base + (str(self.config_path), "add", str(path))
        subprocess_run(command)
        self._update_managed_status_data()

    def re_add(self, path: Path) -> None:
        command = self.base + (str(self.config_path), "re-add", str(path))
        subprocess_run(command)
        self._update_managed_status_data()

    def apply(self, path: Path) -> None:
        command = self.base + (str(self.config_path), "apply", str(path))
        subprocess_run(command)
        self._update_managed_status_data()


class LiveCommands:
    """Group of commands that call subprocess.run() but do not store data in an
    InputOutput dataclass."""

    def git_log(self, path: Path) -> list[str]:
        source_path: str = subprocess_run(BASE + ("source-path", str(path)))
        long_command = BASE + SUBS["git_log"] + (source_path,)
        return subprocess_run(long_command).splitlines()

    def apply_diff(self, file_path: Path) -> list[str]:
        long_command = BASE + ("diff", str(file_path))
        return subprocess_run(long_command).splitlines()

    def re_add_diff(self, file_path: Path) -> list[str]:
        long_command = BASE + ("diff", str(file_path), "--reverse")
        return subprocess_run(long_command).splitlines()

    def cat(self, file_path: Path) -> str:
        return subprocess_run(BASE + ("cat", str(file_path)))


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

    long_command: tuple[str, ...]
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
    doctor: InputOutput
    dump_config: InputOutput
    git_log: InputOutput
    ignored: InputOutput
    managed_files: InputOutput
    managed_dirs: InputOutput
    dir_status_lines: InputOutput
    file_status_lines: InputOutput
    template_data: InputOutput
    perform = PerformChange()
    run = LiveCommands()
    temp_config_path: Path

    def __init__(self) -> None:

        self.long_commands: dict[str, tuple[str, ...]] = {}

        for arg_id, sub_cmd in SUBS.items():
            long_cmd = BASE + sub_cmd
            self.long_commands[arg_id] = long_cmd
            setattr(self, arg_id, InputOutput(long_cmd, arg_id=arg_id))

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
