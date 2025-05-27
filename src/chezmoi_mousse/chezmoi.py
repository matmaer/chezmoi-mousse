import ast
from dataclasses import dataclass, field
from pathlib import Path
from subprocess import TimeoutExpired, run


def subprocess_run(long_command):
    try:
        return run(
            long_command,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,
            text=True,  # returns stdout as str instead of bytes
            timeout=1,
        ).stdout.strip()
    except TimeoutExpired:
        if long_command[-1] == "doctor":
            return "'chezmoi doctor' timed out, the command depends on an internet connection."
        raise


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


@dataclass
class ChezmoiStatus:
    path: str
    is_file: bool
    found: bool
    status: str
    diff_output: str


class Chezmoi:

    cat_config: InputOutput
    doctor: InputOutput
    dump_config: InputOutput
    ignored: InputOutput
    managed_files: InputOutput
    managed_dirs: InputOutput
    managed_files_source: InputOutput
    managed_dirs_source: InputOutput
    status_dirs: InputOutput
    status_files: InputOutput
    template_data: InputOutput
    chezmoi_status: ChezmoiStatus

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
        "ignored": ["ignored"],
        "managed_dirs": ["managed", "--path-style=absolute", "--include=dirs"],
        "managed_files": [
            "managed",
            "--path-style=absolute",
            "--include=files",
        ],
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

    def __init__(self) -> None:

        self.long_commands = {}

        for arg_id, sub_cmd in self.subs.items():
            long_cmd = self.base + sub_cmd
            self.long_commands[arg_id] = long_cmd
            setattr(self, arg_id, InputOutput(long_cmd, arg_id=arg_id))

    @property
    def dest_dir(self) -> Path:
        return Path(self.dump_config.dict_out["destDir"])

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
    def status_paths(self) -> dict[str, dict[Path, str]]:
        """
        Returns a dictionary with four keys: "apply_files", "apply_dirs",
        "re_add_files", and "re_add_dirs". Each key contains a dictionary
        with a Path for the key the corresponding status codes as value.
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

    def run_git_log(self, source_path: str | None = None) -> list[str]:
        long_command = self.base + [
            "git",
            "--",
            "log",
            "--max-count=400",
            "--no-color",
            "--no-decorate",
            "--date-order",
            "--no-expand-tabs",
            "--format=%ar by %cn;%s",
        ]

        if source_path is not None:
            long_command.extend(["--follow", "--", source_path])

        return subprocess_run(long_command).splitlines()

    def managed_file_paths_in_dir(self, dir_path: Path) -> list[Path]:
        return [f for f in self.managed_file_paths if f.parent == dir_path]

    def managed_dir_paths_in_dir(self, dir_path: Path) -> list[Path]:
        return [d for d in self.managed_dir_paths if d.parent == dir_path]

    def unmanaged_in_d(self, dir_path: Path) -> list[Path]:
        if not dir_path.is_dir():
            raise ValueError(
                f"Cannot show unmanaged file or dir: not found. {dir_path}"
            )
        path_strings = subprocess_run(
            self.base + ["unmanaged", "--path-style=absolute", str(dir_path)]
        ).splitlines()
        return [
            p
            for entry in path_strings
            if (p := Path(entry)).parent == dir_path and p.is_file()
        ]

    def run_add(self, file_path: Path) -> str:
        long_command = self.base + [
            "--dry-run",
            "--verbose",
            "add",
            "--include=files",
            "--recursive=false",
            "--prompt=false",
            "--secrets=error",
        ]
        return subprocess_run(long_command + [str(file_path)])

    def run_re_add(self, file_path: Path) -> str:
        long_command = self.base + [
            "--dry-run",
            "--verbose",
            "re-add",
            "--include=files",
            "--recursive=false",
        ]
        return subprocess_run(long_command + [file_path])

    def run_apply(self, file_path: Path) -> str:
        long_command = self.base + [
            "--dry-run",
            "--verbose",
            "apply",
            "--include=files",
            "--recursive=false",
        ]
        return subprocess_run(long_command + [file_path])

    def run_apply_diff(self, file_path: str) -> list[str]:
        long_command = self.base + ["diff", file_path]
        return subprocess_run(long_command).splitlines()

    def run_re_add_diff(self, file_path: str) -> list[str]:
        long_command = self.base + ["diff", file_path]
        return subprocess_run(long_command + ["--reverse"]).splitlines()

    def run_cat(self, file_path: str) -> str:
        return subprocess_run(self.base + ["cat", file_path])

    def run_status(self, path: str) -> str:
        return subprocess_run(self.base + ["status", path])


chezmoi = Chezmoi()
