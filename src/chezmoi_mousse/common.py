from collections.abc import Iterable
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


class Tools:

    @staticmethod
    def subprocess_run(long_command):
        return subprocess.run(
            long_command,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,
            text=True,  # returns stdout as str instead of bytes
            timeout=1,
        ).stdout.strip()

    @staticmethod
    def filter_junk(paths_to_filter: list[Path]) -> list[Path]:
        junk_dirs = {
            "__pycache__",
            ".build",
            ".bundle",
            ".cache",
            ".dart_tool",
            ".DS_Store",
            ".git",
            ".ipynb_checkpoints",
            ".mypy_cache",
            ".parcel_cache",
            ".pytest_cache",
            ".Trash",
            ".venv",
            "bin",
            "cache",
            "Cache",
            "CMakeFiles",
            "Crash Reports",
            "DerivedData",
            "go-build",
            "node_modules",
            "Recent",
            "temp",
            "Temp",
            "tmp",
            "trash",
            "Trash",
        }
        junk_files = {
            ".bak",
            ".cache",
            ".egg-info",
            ".gz",
            ".lnk",
            ".lock",
            ".log",
            ".pid",
            ".rar",
            ".swp",
            ".tar",
            ".temp",
            ".tgz",
            ".tmp",
            ".zip",
        }
        cleaned = []
        for p in paths_to_filter:
            if p.is_dir() and p.name in junk_dirs:
                continue
            if p.is_file() and (p.suffix in junk_files or ".cache-" in str(p)):
                continue
            cleaned.append(p)
        return cleaned


@dataclass
class InputOutput:

    long_command: list[str]
    std_out: str = ""

    @property
    def label(self):
        return " ".join(
            [w for w in self.long_command if not w.startswith("-")]
        )

    def update(self) -> str:
        self.std_out = Tools.subprocess_run(self.long_command)
        return self.std_out


class Chezmoi:

    cat_config: InputOutput
    cm_diff: InputOutput
    config: dict = {}
    doctor: InputOutput
    dump_config: InputOutput
    git_log: InputOutput
    git_status: InputOutput
    ignored: InputOutput
    managed: InputOutput
    status: InputOutput
    template_data: InputOutput
    unmanaged: InputOutput

    base = [
        "chezmoi",
        "--no-pager",
        "--color=off",
        "--no-tty",
        "--mode=file",
        # TODO "--force",  make changes without prompting: flag is not
        # compatible with "--interactive", find way to handle this.
    ]

    # https://www.chezmoi.io/reference/command-line-flags/common/#available-entry-types
    subs = {
        "cat_config": ["cat-config"],
        "template_data": ["data", "--format=json"],
        "doctor": ["doctor"],
        "dump_config": ["dump-config", "--format=json"],
        "git_log": [
            "git",
            "log",
            "--",
            "-20",
            "--no-color",
            "--no-decorate",
            "--date-order",
            "--no-expand-tabs",
            "--format=%ar by %cn;%s",
        ],
        "git_status": ["git", "status"],
        "ignored": ["ignored"],
        "managed": [
            "managed",
            "--path-style=absolute",
            "--include=dirs,files",
            "--exclude=encrypted",
        ],
        "unmanaged": ["unmanaged", "--path-style=absolute"],
        "status": [
            "status",
            "--path-style=absolute",
            "--include=dirs,files",
        ],
        "cm_diff": ["diff"],
    }

    def __init__(self) -> None:

        self.long_commands = {}

        for arg_id, sub_cmd in self.subs.items():
            long_cmd = self.base + sub_cmd
            self.long_commands[arg_id] = long_cmd
            setattr(
                self,
                arg_id,
                InputOutput(long_cmd),
            )

    @property
    def get_config_dump(self) -> dict:
        return json.loads(self.dump_config.std_out)

    @property
    def dest_dir(self) -> Path:
        return self.config["destDir"]

    @property
    def autoadd_enabled(self) -> bool:
        return self.config["git"]["autoadd"]

    @property
    def autocommit_enabled(self) -> bool:
        return self.config["git"]["autocommit"]

    @property
    def autpush_enabled(self) -> bool:
        return self.config["git"]["autopush"]

    @property
    def get_managed_paths(self) -> list[Path]:
        return [Path(p) for p in self.managed.std_out.splitlines()]

    @property
    def get_managed_files(self) -> list[Path]:
        return [p for p in self.get_managed_paths if p.is_file]

    @property
    def get_managed_parents(self) -> set[Path]:
        return {f.parent for f in self.get_managed_files}

    @property
    def get_template_data(self) -> dict:
        return json.loads(self.template_data.std_out)

    @property
    def get_doctor_rows(self) -> list[str]:
        return self.doctor.std_out.splitlines()

    @property
    def get_status(self) -> list[str]:
        return self.status.std_out.splitlines()

    @property
    def get_apply_changes(self) -> list[tuple[str, Path]]:
        changes = [
            l for l in self.status.std_out.splitlines() if l[0] in "ADM"
        ]
        return [(change[0], Path(change[3:])) for change in changes]

    @property
    def get_add_changes(self) -> list[tuple[str, Path]]:
        changes = [
            l for l in self.status.std_out.splitlines() if l[1] in "ADM"
        ]
        return [(change[1], Path(change[3:])) for change in changes]

    def get_cm_diff(self, file_path: str, apply: bool) -> list[str]:
        long_command = self.base + ["diff", file_path]
        if apply:
            return Tools.subprocess_run(long_command).splitlines()
        return Tools.subprocess_run(long_command + ["--reverse"]).splitlines()


chezmoi = Chezmoi()
