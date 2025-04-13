import ast
import re
from dataclasses import dataclass
from pathlib import Path
from subprocess import TimeoutExpired, run


SPLASH = """\
 _______________________________ ___________________._
|       |   |   |    ___|___    |    '    |       |   |
|    ===|       |     __|     __|         |   |   |   |
|       |   |   |       |       |   |ˇ|   |       |   |
`-------^---^---^-------^-------^---' '---^-------^---'
   ____ ____ _______ ___ ___ _______ _______ _______
  |    ˇ    |       |   |   |    ___|    ___|    ___|
  |         |   |   |   |   |__     |__     |     __|
  |   |ˇ|   |       |       |       |       |       |
  '---' '---^-------^-------^-------^-------^-------'
""".replace(
    "===", "=\u200b=\u200b="
).splitlines()

# provisional diagrams until dynamically created
FLOW = """\
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│home directory│    │ working copy │    │  local repo  │    │ remote repo  │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │                   │
       │    chezmoi add    │                   │                   │
       │   chezmoi re-add  │                   │                   │
       │──────────────────>│                   │                   │
       │                   │                   │                   │
       │   chezmoi apply   │                   │                   │
       │<──────────────────│                   │                   │
       │                   │                   │                   │
       │  chezmoi status   │                   │                   │
       │   chezmoi diff    │                   │                   │
       │<─ ─ ─ ─ ─ ─ ─ ─ ─>│                   │     git push      │
       │                   │                   │──────────────────>│
       │                   │                   │                   │
       │                   │           chezmoi git pull            │
       │                   │<──────────────────────────────────────│
       │                   │                   │                   │
       │                   │    git commit     │                   │
       │                   │──────────────────>│                   │
       │                   │                   │                   │
       │                   │    autoCommit     │                   │
       │                   │──────────────────>│                   │
       │                   │                   │                   │
       │                   │                autoPush               │
       │                   │──────────────────────────────────────>│
       │                   │                   │                   │
       │                   │                   │                   │
┌──────┴───────┐    ┌──────┴───────┐    ┌──────┴───────┐    ┌──────┴───────┐
│ destination  │    │ target state │    │ source state │    │  git remote  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
"""


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
    std_out: str = ""

    @property
    def label(self):
        return " ".join(
            [w for w in self.long_command if not w.startswith("-")]
        )

    def update(self) -> str:
        self.std_out = subprocess_run(self.long_command)
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

    @property
    def config(self) -> dict:
        return self.string_to_dict(self.dump_config.std_out)

    @property
    def template_data_dict(self) -> dict:
        return self.string_to_dict(self.template_data.std_out)

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
            Path(line) for line in subprocess_run(long_command).splitlines()
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
            return subprocess_run(long_command).splitlines()
        return subprocess_run(long_command + ["--reverse"]).splitlines()

    def add(self, file_path: Path) -> str:
        long_command = (
            self.base
            + ["--dry-run", "--verbose"]
            + [
                "add",
                "--include=files",
                "--recursive=false",
                "--prompt=false",
                "--secrets=error",
            ]
        )
        # Scan for secrets when adding unencrypted files
        return subprocess_run(long_command + [str(file_path)])

    def re_add(self, file_path: Path) -> str:
        long_command = (
            self.base
            + ["--dry-run", "--verbose"]
            + ["re-add", "--include=files", "--recursive=false"]
        )
        return subprocess_run(long_command + [file_path])

    def apply(self, file_path: Path) -> str:
        long_command = (
            self.base
            + ["--dry-run", "--verbose"]
            + ["apply", "--include=files", "--recursive=false"]
        )
        return subprocess_run(long_command + [file_path])

    def is_unwanted_path(self, path: Path) -> bool:
        unwanted_dirs = {
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
        unwanted_files = {
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

        if path.is_dir() and path.name in unwanted_dirs:
            return True

        regex = r"\.[^.]*$"
        if path.is_file() and bool(re.match(regex, path.name)):
            extension = re.match(regex, path.name)
            if extension in unwanted_files:
                return True

        if not path.is_dir() and not path.is_file():
            # for the time being, only support files and directories
            return True

        return False

    def file_content(self, path: Path) -> str:
        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        if not path.exists():
            raise ValueError(f"File does not exist: {path}")
        with open(path, "rt", encoding="utf-8") as f:
            return f.read()

    def string_to_dict(self, std_out: str) -> dict:
        try:
            return ast.literal_eval(
                std_out.replace("null", "None")
                .replace("false", "False")
                .replace("true", "True")
            )
        except (SyntaxError, ValueError) as error:
            raise ValueError(
                f"Syntax error or invalid value provided: {error}"
            ) from error


chezmoi = Chezmoi()
