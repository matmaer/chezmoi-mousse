from dataclasses import dataclass
from pathlib import Path

from chezmoi_mousse import tools


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
        self.std_out = tools.subprocess_run(self.long_command)
        return self.std_out


class Chezmoi:

    cat_config: InputOutput
    doctor: InputOutput
    dump_config: InputOutput
    git_log: InputOutput
    ignored: InputOutput
    managed_files: InputOutput
    managed_dirs: InputOutput
    status_dirs: InputOutput
    status_files: InputOutput
    template_data: InputOutput
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
        "ignored": ["ignored"],
        "managed_dirs": ["managed", "--path-style=absolute", "--include=dirs"],
        "managed_files": [
            "managed",
            "--path-style=absolute",
            "--include=files",
        ],
        "status_dirs": ["status", "--path-style=absolute", "--include=dirs"],
        "status_files": ["status", "--path-style=absolute", "--include=files"],
        "template_data": ["data", "--format=json"],
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
    def autopush_enabled(self) -> bool:
        return self.config["git"]["autopush"]

    @property
    def managed_d_paths(self) -> list[Path]:
        return [Path(p) for p in self.managed_dirs.std_out.splitlines()]

    @property
    def managed_f_paths(self) -> list[Path]:
        return [Path(p) for p in self.managed_files.std_out.splitlines()]

    def unmanaged_in_d(self, dir_path: Path) -> list[Path]:
        long_command = self.base + [
            "unmanaged",
            "--path-style=absolute",
            str(dir_path),
        ]
        if (
            not dir_path.exists()
            or not dir_path.is_dir()
            or not dir_path.is_absolute()
        ):
            raise ValueError(f"Invalid directory path: {dir_path}")
        file_paths = [
            Path(line)
            for line in tools.subprocess_run(long_command).splitlines()
        ]
        return [p for p in file_paths if p.is_file() and p.parent == dir_path]

    def get_status(
        self, apply: bool, dirs: bool = False, files: bool = False
    ) -> list[tuple[str, Path]]:
        if not dirs and not files:
            raise ValueError("Either files or dirs must be true")

        # Combine lines from dirs and files
        lines = []
        if dirs:
            lines.extend(self.status_dirs.std_out.splitlines())
        if files:
            lines.extend(self.status_files.std_out.splitlines())

        relevant_status_codes = {"A", "D", "M"}
        relevant_lines = [
            line for line in lines if line[:2].strip() in relevant_status_codes
        ]

        return [
            (line[1] if apply else line[0], Path(line[3:]))
            for line in relevant_lines
        ]

    def diff(self, file_path: str, apply: bool) -> list[str]:
        long_command = self.base + ["diff", file_path]
        if apply:
            return tools.subprocess_run(long_command).splitlines()
        return tools.subprocess_run(long_command + ["--reverse"]).splitlines()

    def add(self, file_path: Path) -> str:
        long_command = (
            self.base + ["--dry-run", "--verbose"] + self.write_commands["add"]
        )
        return tools.subprocess_run(long_command + [str(file_path)])

    def re_add(self, file_path: Path) -> str:
        long_command = (
            self.base
            + ["--dry-run", "--verbose"]
            + self.write_commands["re_add"]
        )
        return tools.subprocess_run(long_command + [file_path])

    def apply(self, file_path: Path) -> str:
        long_command = (
            self.base
            + ["--dry-run", "--verbose"]
            + self.write_commands["apply"]
        )
        return tools.subprocess_run(long_command + [file_path])


chezmoi = Chezmoi()
