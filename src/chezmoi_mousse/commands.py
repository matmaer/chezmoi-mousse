import ast
import subprocess
import tomllib
from dataclasses import dataclass, field

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
        if new_stdout not in (self.std_out, None, ""):
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
        elif new_stdout in (None, ""):
            raise ValueError("Empty new_stdout, this needs to be handled.")
        elif new_stdout == self.std_out:
            log.warning("useless update, no change in stdout")
        else:
            self.std_out = new_stdout
            self.py_out = new_stdout.splitlines()


@dataclass
class Command:
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
class CommandComponents(Command):

    name: str
    base: list = field(default_factory=list)
    subs: list = field(default_factory=list)
    sub_labels: dict = field(default_factory=dict, init=False)
    log_labels: dict = field(default_factory=dict, init=False)
    commands: dict = field(default_factory=dict, init=False)

    def __post_init__(self):
        log.debug(f"initializing {self.name} command components")
        for sub_words in self.subs:
            sub_no_flags = [_ for _ in sub_words if not _.startswith("-")]
            sub_label = " ".join(sub_no_flags)
            cmd_id = f"{self.name}_{sub_label.replace('-', '_')}"
            self.sub_labels[cmd_id] = sub_label
            self.log_labels[cmd_id] = f"{self.name} {sub_label}"
            self.commands[cmd_id] = self.base + sub_words

    def get_output(self, sub_label: str, refresh=False) -> str | list | dict:
        log.debug(f"getting output for {self.name} {sub_label}")
        cmd_id = self.commands[sub_label]
        full_command = self.commands[cmd_id]
        if self.storage.py_out is None or refresh:
            return self.run(full_command)
        return self.storage.py_out


@dataclass
class Chezmoi(Command):
    name = "chezmoi"
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
    _components = CommandComponents(name, base, subs)
    commands = _components.commands
    labels = _components.sub_labels
    log_labels = _components.log_labels
    get = _components.get_output


chezmoi = Chezmoi()
