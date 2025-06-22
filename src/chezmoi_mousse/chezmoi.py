import ast
from dataclasses import dataclass, field
from pathlib import Path
from subprocess import TimeoutExpired, run
from typing import Literal, NamedTuple

from chezmoi_mousse.id_typing import TabEnum


def callback_null_object(*args) -> None:
    pass


# Used and re-assigned in gui.py to log commands
command_log_callback = callback_null_object


BASE = ("chezmoi", "--no-pager", "--color=off", "--no-tty", "--mode=file")

# https://www.chezmoi.io/reference/command-line-flags/common/#available-entry-types
SUBS = {
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
    "managed_dirs_source": (
        "managed",
        "--path-style=source-absolute",
        "--include=dirs",
    ),
    "managed_files_source": (
        "managed",
        "--path-style=source-absolute",
        "--include=files",
    ),
    "dir_status_lines": ("status", "--path-style=absolute", "--include=dirs"),
    "file_status_lines": (
        "status",
        "--path-style=absolute",
        "--include=files",
    ),
    "template_data": ("data", "--format=json"),
}


def subprocess_run(long_command: tuple[str, ...]) -> str:
    try:
        result = run(
            long_command,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,
            text=True,  # returns stdout as str instead of bytes
            timeout=1,
        ).stdout.strip()
        if any(cmd in long_command for cmd in ("diff", "cat", "git")):
            command_log_callback((long_command, "output displayed in gui"))
        else:
            command_log_callback((long_command, result))
        return result
    except TimeoutExpired as error:
        raise TimeoutExpired(
            error.cmd,
            error.timeout,
            output="The timeout value for subprocess calls of one second was exceeded.",
            stderr=error.stderr,
        ) from error


class PerformChange:
    """Group of commands which either make changes on disk or in the chezmoi
    repository.

    Verbose output is returned for logging.
    """

    base = BASE + ("--verbose", "--dry-run")
    # TODO: remove --dry-run

    @staticmethod
    def add(path: Path) -> str:
        return subprocess_run(PerformChange.base + ("add", str(path)))

    @staticmethod
    def re_add(path: Path) -> str:
        return subprocess_run(PerformChange.base + ("re-add", str(path)))

    @staticmethod
    def apply(path: Path) -> str:
        return subprocess_run(PerformChange.base + ("apply", str(path)))


class SubProcessCalls:
    """Group of commands that call subprocess.run() but do not change any
    state."""

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
    dict_out: dict = field(default_factory=dict)
    list_out: list[str] = field(default_factory=list)

    @property
    def label(self):
        return f'chezmoi {self.arg_id.replace("_", " ")}'

    def update(self) -> None:
        self.std_out = subprocess_run(self.long_command)
        self.list_out = self.std_out.splitlines()
        try:
            # convert dict-like output from chezmoi commands, eg json output
            self.dict_out = ast.literal_eval(
                self.std_out.replace("null", "None")
                .replace("false", "False")
                .replace("true", "True")
            )
        except (SyntaxError, ValueError):
            self.dict_out = {}


class Chezmoi:

    cat_config: InputOutput
    doctor: InputOutput
    dump_config: InputOutput
    git_log: InputOutput
    ignored: InputOutput
    managed_files: InputOutput
    managed_dirs: InputOutput
    managed_files_source: InputOutput
    managed_dirs_source: InputOutput
    dir_status_lines: InputOutput
    file_status_lines: InputOutput
    template_data: InputOutput
    perform = PerformChange()
    run = SubProcessCalls()

    def __init__(self) -> None:

        self.long_commands = {}

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
            if kind == "dirs":
                managed_paths = self.managed_dir_paths
                status_lines = self.dir_status_lines.list_out
            elif kind == "files":
                managed_paths = self.managed_file_paths
                status_lines = self.file_status_lines.list_out

            if tab_name == TabEnum.apply_tab.name:
                status_codes = "ADM"
                status_idx = 1
            elif tab_name == TabEnum.re_add_tab.name:
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

        apply_dirs = create_status_dict(
            tab_name=TabEnum.apply_tab.name, kind="dirs"
        )
        apply_files = create_status_dict(
            tab_name=TabEnum.apply_tab.name, kind="files"
        )
        re_add_dirs = create_status_dict(
            tab_name=TabEnum.re_add_tab.name, kind="dirs"
        )
        re_add_files = create_status_dict(
            tab_name=TabEnum.re_add_tab.name, kind="files"
        )

        return {
            TabEnum.apply_tab.name: StatusDicts(
                dirs=apply_dirs, files=apply_files
            ),
            TabEnum.re_add_tab.name: StatusDicts(
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
        tab_enum: TabEnum,
        dir_path: Path,
    ) -> list[Path]:
        self._validate_managed_dir_path(dir_path)
        return [
            p
            for p in self.managed_status[tab_enum.name].dirs_with_status
            if p.parent == dir_path
        ]

    def files_with_status_in(
        # checks only direct children
        self,
        tab_enum: TabEnum,
        dir_path: Path,
    ) -> list[Path]:
        self._validate_managed_dir_path(dir_path)
        return [
            p
            for p in self.managed_status[tab_enum.name].files_with_status
            if p.parent == dir_path
        ]

    def dirs_without_status_in(
        self,
        tab_enum: TabEnum,
        dir_path: Path,
        # checks only direct children
    ) -> list[Path]:
        self._validate_managed_dir_path(dir_path)
        return [
            p
            for p in self.managed_status[tab_enum.name].dirs_without_status
            if p.parent == dir_path
        ]

    def files_without_status_in(
        self, tab_enum: TabEnum, dir_path: Path
    ) -> list[Path]:
        # checks only direct children
        self._validate_managed_dir_path(dir_path)
        return [
            p
            for p in self.managed_status[tab_enum.name].files_without_status
            if p.parent == dir_path
        ]

    def dir_has_managed_files(self, dir_path: Path) -> bool:
        # checks for any, no matter how deep in subdirectories
        self._validate_managed_dir_path(dir_path)
        return any(f for f in self.managed_file_paths if dir_path in f.parents)

    def dir_has_status_files(self, tab_enum: TabEnum, dir_path: Path) -> bool:
        # checks for any, no matter how deep in subdirectories
        self._validate_managed_dir_path(dir_path)
        return any(
            f
            for f, status in self.managed_status[tab_enum.name].files.items()
            if dir_path in f.parents and status != "X"
        )

    def dir_has_status_dirs(self, tab_enum: TabEnum, dir_path: Path) -> bool:
        # checks for any, no matter how deep in subdirectories
        self._validate_managed_dir_path(dir_path)
        status_dirs = self.managed_status[tab_enum.name].dirs.items()
        if dir_path.parent == self.dest_dir and dir_path in status_dirs:
            # the parent is dest_dir, also return True because dest_dir is
            # not present in the self.managed_status dict
            return True
        return any(
            f
            for f, status in status_dirs
            if dir_path in f.parents and status != "X"
        )


chezmoi = Chezmoi()
