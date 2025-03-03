from dataclasses import dataclass
import json
import subprocess
import tomllib


@dataclass
class InputOutput:
    long_command: list[str]
    std_out: str = "initial std_out value"

    @property
    def py_out(self):
        failures = {}
        std_out = self.std_out.strip()
        if std_out == "":
            failures["std_out"] = "empty std_out nothing to decode"
        try:
            return json.loads(std_out)
        except json.JSONDecodeError:
            failures["json"] = "std_out json.JSONDecodeError"
        try:
            return tomllib.loads(std_out)
        except tomllib.TOMLDecodeError:
            failures["toml"] = "std_out tomllib.TOMLDecodeError"
            # check how many "\n" newlines are found in the output
        if std_out.count("\n") > 0:
            return std_out.splitlines()
        return std_out

    @property
    def label(self):
        return " ".join([w for w in self.long_command if not w.startswith("-")])

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

    def update(self):
        """Re-run the subprocess call, don't return anything."""
        self._subprocess_run()

    def updated_std_out(self):
        """Re-run subprocess call and return std_out."""
        self._subprocess_run()
        return self.std_out

    def updated_py_out(self):
        """Re-run subprocess call and return py_out."""
        self._subprocess_run()
        return self.py_out


class Chezmoi:

    cat_config: InputOutput = None
    data: InputOutput = None
    doctor: InputOutput = None
    dump_config: InputOutput = None
    git_log: InputOutput = None
    git_status: InputOutput = None
    ignored: InputOutput = None
    managed: InputOutput = None
    status: InputOutput = None
    unmanaged: InputOutput = None

    def __init__(self):
        self.base = [
            "chezmoi",
            "--no-pager",
            "--color=false",
            "--no-tty",
            "--progress=false",
        ]
        self.subs = {
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

        for arg_id, sub_cmd in self.subs.items():
            setattr(self, arg_id, InputOutput(self.base + sub_cmd))

    @property
    def arg_ids(self):
        """Return the list of arg_ids."""
        return list(self.subs.keys())

    def updated_input_output(self, arg_id):
        """Update and return the InputOutput instance in this Chezmoi class."""
        getattr(self, arg_id).update()
        return getattr(self, arg_id)
