import ast
from dataclasses import dataclass, field
from pathlib import Path
from subprocess import TimeoutExpired, run

dest_dir = Path.home()


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
            "-400",
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
        return self.dump_config.dict_out["git"]["autoadd"]

    @property
    def autocommit_enabled(self) -> bool:
        return self.dump_config.dict_out["git"]["autocommit"]

    @property
    def autopush_enabled(self) -> bool:
        return self.dump_config.dict_out["git"]["autopush"]

    @property
    def managed_dir_paths(self) -> set[Path]:
        return {Path(p) for p in self.managed_dirs.list_out}

    @property
    def managed_file_paths(self) -> set[Path]:
        return {Path(p) for p in self.managed_files.list_out}

    @property
    def missing_file_paths(self) -> set[Path]:
        return {
            Path(p)
            for p in self.managed_files.list_out
            if not Path(p).exists()
        }

    @property
    def apply_status_file_paths(self) -> dict[Path, str]:
        return self._status_paths(apply=True)

    @property
    def re_add_status_file_paths(self) -> dict[Path, str]:
        return self._status_paths(apply=False)

    def _status_paths(self, apply: bool) -> dict[Path, str]:
        status_paths = {}
        for line in self.status_files.list_out:
            adm = line[1] if apply else line[0]
            if adm in "ADM":
                # status_paths[adm] = Path(line[3:])
                status_paths[Path(line[3:])] = adm
        return status_paths

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

    def diff(self, file_path: str, apply: bool) -> list[str]:
        long_command = chezmoi.base + ["diff"] + [file_path]
        if apply:
            return subprocess_run(long_command).splitlines()
        return subprocess_run(long_command + ["--reverse"]).splitlines()


chezmoi = Chezmoi()
