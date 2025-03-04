from dataclasses import dataclass, field
import json
import subprocess
import tomllib
import yaml



@dataclass
class InputOutput:
    long_command: list[str] = field(default_factory=list)
    std_out: str = "Initialize InputOutput std_out"

    @property
    def py_out(self):
        failures = {}
        std_out = self.std_out.strip()
        if std_out == "":
            return "std_out is an empty string"
        try:
            return json.loads(std_out)
        except json.JSONDecodeError:
            failures["json"] = "std_out json.JSONDecodeError"
        try:
            return tomllib.loads(std_out)
        except tomllib.TOMLDecodeError:
            failures["toml"] = "std_out tomllib.TOMLDecodeError"
        try:
            return yaml.safe_load(std_out)
        except yaml.YAMLError:
            failures["yaml"] = "std_out yaml.YAMLError"
        if std_out.count("\n") > 0:
            return std_out.splitlines()
        return std_out

    @property
    def label(self):
        return " ".join(
            [w for w in self.long_command if not w.startswith("-")]
        )

    def _subprocess_run(self):
        """Runs the subprocess call and sets std_out."""
        result = subprocess.run(
            self.long_command,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,  # mitigates shell injection risk
            text=True,  # returns stdout as str instead of bytes
            timeout=2,
        )
        self.std_out = result.stdout

    def update(self) -> None:
        """Re-run the subprocess call, don't return anything."""
        self._subprocess_run()

    def updated_std_out(self) -> str:
        """Re-run subprocess call and return std_out."""
        self._subprocess_run()
        return self.std_out

    def updated_py_out(self) -> str | list | dict:
        """Re-run subprocess call and return py_out."""
        self._subprocess_run()
        return self.py_out


class Chezmoi:

    # avoid linting errors for the following attributes
    cat_config: InputOutput
    data: InputOutput
    doctor: InputOutput
    dump_config: InputOutput
    git_log: InputOutput
    git_status: InputOutput
    ignored: InputOutput
    managed: InputOutput
    status: InputOutput
    unmanaged: InputOutput


    def __init__(self) -> None:
        self.words = {
            "base": [
                "chezmoi",
                "--no-pager",
                "--color=false",
                "--no-tty",
                "--progress=false",
            ],
            "cat_config": ["cat-config"],
            "data": ["data", "--format=json"],
            "doctor": ["doctor"],
            "dump_config": ["dump-config", "--format=json"],
            "git_log": ["git", "log", "--", "--oneline"],
            "git_status": ["git", "status"],
            "ignored": ["ignored"],
            "managed": ["managed", "--path-style=absolute"],
            "status": ["status", "--parent-dirs"],
            "unmanaged": ["unmanaged", "--path-style=absolute"],
        }

        self.base = self.words.pop("base")
        self.name = self.base[0]
        self.std_out = "init std_out from Chezmoi"
        self.py_out = "init py_out from Chezmoi"

        for arg_id, sub_cmd in self.words.items():
            command_io = InputOutput(self.base + sub_cmd)
            # setattr(self, f"{arg_id}", self.io[arg_id])
            setattr(self, arg_id, command_io)


    @property
    def arg_ids(self):
        return list(self.words.keys())

chezmoi = Chezmoi()
