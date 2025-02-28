import ast
import subprocess
from dataclasses import dataclass, field


@dataclass
class InputOutput:
    long_cmd: list[str]
    std_out: str = ""

    @property
    def label(self) -> str:
        return " ".join([w for w in self.long_cmd if not w.startswith("-")])

    @property
    def py_out(self):
        try:
            return ast.literal_eval(self.std_out)
        except (SyntaxError, ValueError):
            return self.std_out

    def new_py_out(self) -> str:
        result = subprocess.run(
            self.long_cmd,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,  # mitigates shell injection risk
            text=True,  # returns stdout as str instead of bytes
            timeout=2,
        )
        self.std_out = result.stdout
        return self.py_out


@dataclass
class Chezmoi:

    name = "chezmoi"
    # TODO: general command logic can be moved to command class when more
    # commands are added like ls, tree, etc.
    base = [name] + [
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

    io_instances: dict[str, InputOutput] = field(
        init=False, default_factory=dict
    )

    def __post_init__(self):
        self.long_commands = [self.base + sub for sub in self.subs]
        self.sub_ids = []

        for words in self.long_commands:
            verbs = [w for w in words[1:] if not w.startswith("-")]
            self.sub_ids += ["_".join([w.replace("-", "_") for w in verbs])]

        for sub_id, long_cmd in zip(self.sub_ids, self.long_commands):
            io_instance = InputOutput(long_cmd)
            setattr(self, sub_id, io_instance)
            self.io_instances[sub_id] = io_instance

    def refresh_py_out(self, sub_id: str):
        self.io_instances[sub_id].new_py_out()


# Instantiate Chezmoi and call the method at a later stage
chezmoi = Chezmoi()
# chezmoi.call_new_py_out()
