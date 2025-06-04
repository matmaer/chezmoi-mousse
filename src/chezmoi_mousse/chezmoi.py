"""Contains anything related to running chezmoi commands and processing the
output of those commands.

The module will not import any textual classes, but does contain a
command_log_callback function set by gui.py.
"""

import ast
from dataclasses import dataclass, field
import os
from pathlib import Path
from subprocess import TimeoutExpired, run


def callback_null_object(*args) -> None:
    pass


# Used and re-assigned in gui.py to log commands
command_log_callback = callback_null_object


BASE = ["chezmoi", "--no-pager", "--color=off", "--no-tty", "--mode=file"]

# https://www.chezmoi.io/reference/command-line-flags/common/#available-entry-types
SUBS = {
    "cat_config": ["cat-config"],
    "doctor": ["doctor"],
    "dump_config": ["dump-config", "--format=json"],
    "git_log": [
        "git",
        "--",
        "log",
        "--max-count=100",
        "--no-color",
        "--no-decorate",
        "--date-order",
        "--no-expand-tabs",
        "--format=%ar by %cn;%s",
    ],
    "ignored": ["ignored"],
    "managed_dirs": ["managed", "--path-style=absolute", "--include=dirs"],
    "managed_files": ["managed", "--path-style=absolute", "--include=files"],
    "managed_dirs_source": [
        "managed",
        "--path-style=source-absolute",
        "--include=dirs",
    ],
    "managed_files_source": [
        "managed",
        "--path-style=source-absolute",
        "--include=files",
    ],
    "status_dirs": ["status", "--path-style=absolute", "--include=dirs"],
    "status_files": ["status", "--path-style=absolute", "--include=files"],
    "template_data": ["data", "--format=json"],
}


def subprocess_run(long_command: list[str]) -> str:
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

    base = BASE + ["--verbose", "--dry-run"]
    # TODO: remove --dry-run

    @staticmethod
    def add(path: Path) -> str:
        return subprocess_run(PerformChange.base + ["add"] + [str(path)])

    @staticmethod
    def re_add(path: Path) -> str:
        return subprocess_run(PerformChange.base + ["re-add"] + [str(path)])

    @staticmethod
    def apply(path: Path) -> str:
        return subprocess_run(PerformChange.base + ["apply"] + [str(path)])


class SubProcessCalls:
    """Group of commands that call subprocess.run() but do not change any
    state."""

    def git_log(self, path: Path) -> list[str]:
        source_path = subprocess_run(BASE + ["source-path", str(path)])
        long_command = BASE + SUBS["git_log"] + [str(source_path)]
        return subprocess_run(long_command).splitlines()

    def apply_diff(self, file_path: Path) -> list[str]:
        long_command = BASE + ["diff", str(file_path)]
        return subprocess_run(long_command).splitlines()

    def re_add_diff(self, file_path: Path) -> list[str]:
        long_command = BASE + ["diff", str(file_path)]
        return subprocess_run(long_command + ["--reverse"]).splitlines()

    def cat(self, file_path: Path) -> str:
        return subprocess_run(BASE + ["cat", str(file_path)])

    def unmanaged_in_dir(self, dir_path: Path) -> list[Path]:
        path_strings = subprocess_run(
            BASE + ["unmanaged", "--path-style=absolute", str(dir_path)]
        ).splitlines()
        # chezmoi can return the dir itself, eg when the dir is not managed
        if len(path_strings) == 1 and path_strings[0] == str(dir_path):
            return []
        return [
            p
            for entry in path_strings
            if (p := Path(entry)).parent == dir_path
        ]


@dataclass
class InputOutput:

    long_command: list[str]
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
    status_dirs: InputOutput
    status_files: InputOutput
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
    def source_dir_str(self) -> str:
        return self.dump_config.dict_out["sourceDir"]

    @property
    def dest_dir(self) -> Path:
        return Path(self.dump_config.dict_out["destDir"])

    @property
    def dest_dir_str(self) -> str:
        return self.dump_config.dict_out["destDir"]

    @property
    def dest_dir_str_spaced(self) -> str:
        return f" {self.dump_config.dict_out["destDir"]}{os.sep} "

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
    def status_dir_paths(self) -> list[Path]:
        return [Path(p) for p in self.status_dirs.list_out]

    @property
    def status_file_paths(self) -> list[Path]:
        return [Path(p) for p in self.status_files.list_out]

    @property
    def status_paths(self) -> dict[str, dict[Path, str]]:
        """
        Returns a dictionary with four keys: "apply_files", "apply_dirs",
        "re_add_files", and "re_add_dirs". Each key contains a dictionary
        with a Path for the key and the corresponding status codes as value.
        """

        def create_status_dict(
            lines: list[str], apply: bool
        ) -> dict[Path, str]:
            result = {}
            for line in lines:
                status_code = line[1] if apply else line[0]
                if status_code in "ADM":
                    result[Path(line[3:])] = status_code
            return result

        return {
            "apply_files": create_status_dict(
                self.status_files.list_out, apply=True
            ),
            "apply_dirs": create_status_dict(
                self.status_dirs.list_out, apply=True
            ),
            "re_add_files": create_status_dict(
                self.status_files.list_out, apply=False
            ),
            "re_add_dirs": create_status_dict(
                self.status_dirs.list_out, apply=False
            ),
        }

    @property
    def managed_file_paths_without_status(self) -> list[Path]:
        return [
            p
            for p in self.managed_file_paths
            if p not in self.status_paths["apply_files"]
            or p not in self.status_paths["re_add_files"]
        ]

    def managed_file_paths_in_dir(self, dir_path: Path) -> list[Path]:
        return [f for f in self.managed_file_paths if f.parent == dir_path]

    def managed_dir_paths_in_dir(self, dir_path: Path) -> list[Path]:
        return [d for d in self.managed_dir_paths if d.parent == dir_path]


chezmoi = Chezmoi()
