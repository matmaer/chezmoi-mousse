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
        all_dirs = [p for p in paths_to_filter if p.is_dir()]
        all_files = [p for p in paths_to_filter if p.is_file()]
        clean_dirs = [p for p in all_dirs if p.name not in junk_dirs]
        clean_files = [p for p in all_files if p.suffix not in junk_files]
        return clean_dirs + clean_files


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
    doctor: InputOutput
    dump_config: InputOutput
    git_log: InputOutput
    git_status: InputOutput
    ignored: InputOutput
    managed_files: InputOutput
    managed_dirs: InputOutput
    status_dirs: InputOutput
    status_files: InputOutput
    template_data: InputOutput
    unmanaged: InputOutput
    config: dict = {}
    template_data_dict: dict = {}

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
        "managed_dirs": ["managed", "--path-style=absolute", "--include=dirs"],
        "managed_files": [
            "managed",
            "--path-style=absolute",
            "--include=files",
            "--exclude=encrypted",
        ],
        "status_dirs": [
            "status",
            "--path-style=absolute",
            "--include=dirs",
            "--recursive",
        ],
        "status_files": [
            "status",
            "--path-style=absolute",
            "--include=files",
            "--recursive",
        ],
        "template_data": ["data", "--format=json"],
        "unmanaged": ["unmanaged", "--path-style=absolute"],
    }

    write_commands = {
        "add": [
            "add",
            "--include=files",
            "--recursive=false",
            "--prompt=false",
            "--secrets=error",  # Scan for secrets when adding unencrypted files
        ],
        "apply": ["apply", "--include=files", "--recursive=false"],
        "re_add": ["re-add", "--include=files", "--recursive=false"],
    }

    def __init__(self) -> None:

        self.long_commands = {}

        for arg_id, sub_cmd in self.subs.items():
            long_cmd = self.base + sub_cmd
            self.long_commands[arg_id] = long_cmd
            setattr(self, arg_id, InputOutput(long_cmd))

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
    def managed_d_paths(self) -> list[Path]:
        return [Path(p) for p in self.managed_dirs.std_out.splitlines()]

    @property
    def managed_f_paths(self) -> list[Path]:
        return [Path(p) for p in self.managed_files.std_out.splitlines()]

    @property
    def managed_paths(self) -> list[Path]:
        return self.managed_d_paths + self.managed_f_paths

    def get_status(
        self, apply: bool, dirs: bool, files: bool
    ) -> dict[str, Path]:

        result: dict[str, Path] = {}
        lines = []
        dir_lines = [
            l
            for l in self.status_dirs.std_out.splitlines()
            if l[0] in "ADM" or l[1] in "ADM"
        ]
        file_lines = [
            l
            for l in self.status_files.std_out.splitlines()
            if l[0] in "ADM" or l[1] in "ADM"
        ]
        if files and not dirs:
            lines = file_lines
        elif dirs and not files:
            lines = dir_lines
        elif dirs and files:
            lines = file_lines + dir_lines
        else:
            raise ValueError("Ether files or dirs must be true")

        for line in lines:
            path = Path(Path(line[3:]))
            if apply:
                status_code = line[1]
            else:
                status_code = line[0]
            result[status_code] = path
        return result

    def chezmoi_diff(self, file_path: str, apply: bool) -> list[str]:
        long_command = self.base + ["diff", file_path]
        if apply:
            return Tools.subprocess_run(long_command).splitlines()
        return Tools.subprocess_run(long_command + ["--reverse"]).splitlines()

    def chezmoi_add(self, file_path: Path) -> str:
        long_command = self.base + self.write_commands["add"]
        return Tools.subprocess_run(long_command + [file_path])

    def chezmoi_re_add(self, file_path: Path) -> str:
        long_command = self.base + self.write_commands["re_add"]
        return Tools.subprocess_run(long_command + [file_path])

    def chezmoi_apply(self, file_path: Path) -> str:
        long_command = self.base + self.write_commands["apply"]
        return Tools.subprocess_run(long_command + [file_path])


chezmoi = Chezmoi()
