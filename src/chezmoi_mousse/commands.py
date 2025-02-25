from dataclasses import dataclass, field
import ast
import subprocess
import tomllib

from textual import log


@dataclass
class Storage:
    std_out: str | None = None
    py_out: str | list | dict | None = None

    def update_storage(self, new_stdout: str):
        log.debug(f"updating storage with:\n {new_stdout}")
        if new_stdout == new_stdout.strip():
            log.debug("no leading/trailing whitespace detected")
        if self.std_out is None and new_stdout is not None:
            log.error("std_out is None, this should not happen.")
        # normally subprocess.run does NOT return leading/trailing whitespace
        # but the subsequent logic could fail if it would be the case
        new_stdout = new_stdout.strip()
        if new_stdout not in (self.std_out, None, ''):
            self.std_out = new_stdout.strip()
            try:
                self.py_out = ast.literal_eval(self.std_out)
            except (ValueError, SyntaxError):
                pass
            try:
                self.py_out = tomllib.loads(self.std_out)
            except (ValueError, SyntaxError):
                pass
            self.py_out = self.std_out
        elif new_stdout in (None, ''):
            raise ValueError("Empty new_stdout, this needs to be handled.")
        elif new_stdout == self.std_out:
            log.warning("useless update, no change in stdout")
        else:
            self.std_out = new_stdout
            self.py_out = new_stdout.splitlines()


@dataclass
class SingleCommand:
    storage = Storage()
    def run(self, long_command) -> str | list | dict:
        result = subprocess.run(
            long_command,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,  # mitigates shell injection risk
            text=True,  # returns stdout as str instead of bytes
            timeout=2,
        )
        self.storage.update_storage(result.stdout)
        return self.storage.py_out


@dataclass
class Command(SingleCommand):
    # id: str = field(init=False)
    # label: str = field(init=False)
    # long_command: list[str] = field(default_factory=list)    command: str
    base: list = field(default_factory=list)
    subs: list = field(default_factory=list)
    command_ids: dict = field(default_factory=dict, init=False)
    label_ids: dict = field(default_factory=dict, init=False)
    outputs: dict = field(default_factory=dict, init=False)

    def __post_init__(self):
        name = self.base[0]
        for sub in self.subs:
            labels = [" ".join(_) for _ in sub if not _.startswith("-")]
            ids = [f"{name}_{_}" for _ in labels.replace("-", "_")]
            long_command = self.base + sub
            for cmd_id, label in zip(ids, labels):
                self.command_ids[cmd_id] = long_command
                self.label_ids[cmd_id] = label
                self.outputs[cmd_id] = None

    def get_output(
        self, full_command: list, refresh = False
        ) -> str | list | dict:
        if self.storage.py_out is None or refresh:
            return self.run(full_command)
        return self.storage.py_out


class Chezmoi(Command):
    base = [
        "chezmoi",
        "--no-pager",
        "--color=false",
        "--no-tty",
        "--progress=false",
    ]
    subs = [
        ["doctor"],
        ["dump-config", "--format=json"],
        ["data", "--format=json"],
        ["cat-config"],
        ["ignored"],
        ["managed", "--path-style=absolute"],
        ["status", "--parent-dirs"],
        ["unmanaged", "--path-style=absolute"],
        ["git", "status"],
        ["git", "log", "--", "--oneline"],
    ]


chezmoi = Chezmoi()
