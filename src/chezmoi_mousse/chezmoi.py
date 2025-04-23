import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from subprocess import TimeoutExpired, run

from chezmoi_mousse.config import unwanted_dirs, unwanted_files


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
    arg_id: str = ""
    std_out: str = ""
    dict_out: dict = field(default_factory=dict)
    list_out: list[str] = field(default_factory=list)

    @property
    def label(self):
        return " ".join(
            [w for w in self.long_command if not w.startswith("-")]
        )

    def __post_init__(self) -> None:
        self.list_out = self.std_out.splitlines()
        self.dict_out = {}

    def update(self) -> None:
        self.std_out = subprocess_run(self.long_command)
        self._update_dict()
        self.list_out = self.std_out.splitlines()

    def _update_dict(self) -> None:
        try:
            self.dict_out = ast.literal_eval(
                self.std_out.replace("null", "None")
                .replace("false", "False")
                .replace("true", "True")
            )
        except (SyntaxError, ValueError) as error:
            self.dict_out = {}


@dataclass
class ChezmoiPaths:
    dest_dir: Path
    managed_dirs: list[Path]
    managed_files: list[Path]
    existing_managed_dirs: list[Path]
    existing_managed_files: list[Path]

    def update(
        self,
        dump_config: InputOutput,
        managed_dirs: InputOutput,
        managed_files: InputOutput,
        update_std_out: bool = True,
    ) -> None:
        if update_std_out:
            dump_config.update()
            managed_dirs.update()
            managed_files.update()

        self.dest_dir = Path(dump_config.dict_out["destDir"])
        self.managed_dirs = [Path(p) for p in managed_dirs.list_out]
        self.managed_files = [Path(p) for p in managed_files.list_out]
        self.existing_managed_dirs = [
            Path(p) for p in managed_dirs.list_out if Path(p).is_dir()
        ]
        self.existing_managed_files = [
            Path(p) for p in managed_files.list_out if Path(p).is_file()
        ]


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
    paths: ChezmoiPaths

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

        setattr(
            self,
            "paths",
            ChezmoiPaths(
                dest_dir=Path.home(),
                managed_dirs=[],
                managed_files=[],
                existing_managed_dirs=[],
                existing_managed_files=[],
            ),
        )

    @property
    def autoadd_enabled(self) -> bool:
        return self.dump_config.dict_out["git"]["autoadd"]

    @property
    def autocommit_enabled(self) -> bool:
        return self.dump_config.dict_out["git"]["autocommit"]

    @property
    def autopush_enabled(self) -> bool:
        return self.dump_config.dict_out["git"]["autopush"]

    def unmanaged_in_d(self, dir_path: Path) -> list[Path]:
        if not dir_path.is_dir():
            raise ValueError(f"Directory does not exist: {dir_path}")
        path_strings = subprocess_run(
            self.base + ["unmanaged", "--path-style=absolute", str(dir_path)]
        ).splitlines()
        return [
            p
            for entry in path_strings
            if (p := Path(entry)).parent == dir_path and p.is_file()
        ]

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
        if path.is_dir():
            if path.name in unwanted_dirs:
                return True
            return False

        if path.is_file():
            extension = re.match(r"\.[^.]*$", path.name)
            if extension in unwanted_files:
                return True
            if self._is_reasonable_dotfile(path):
                return False
        return False

    def file_content(self, path: Path) -> str:
        if not self._is_reasonable_dotfile(path):
            return f'File is not a text file or too large for a reasonable "dotfile" : {path}'
        with open(path, "rt", encoding="utf-8") as f:
            return f.read()

    def _is_reasonable_dotfile(self, file_path: Path) -> bool:
        if file_path.stat().st_size < 150 * 1024:  # 150 KiB
            try:
                with open(file_path, "rb") as file:
                    chunk = file.read(512)
                    # Decode explicitly with encoding="utf-8" or the UnicodeDecodeError will not be raised in time
                    return str(chunk, encoding="utf-8").isprintable()
            except UnicodeDecodeError:
                # Assume the file is not a text file in this case
                return False
        return False


chezmoi = Chezmoi()
