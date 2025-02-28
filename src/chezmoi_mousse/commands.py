import subprocess
from dataclasses import dataclass


@dataclass
class InputOutput:
    long_cmd: list[str]
    std_out: str = ""

    @property
    def label(self) -> str:
        return " ".join([w for w in self.long_cmd if not w.startswith("-")])

    @property
    def args_id(self) -> str:
        all_args = self.long_cmd[1:]
        verbs = [w for w in all_args if not w.startswith("-")]
        return "_".join([w.replace("-", "_") for w in verbs])

    def update(self) -> str:
        result = subprocess.run(
            self.long_cmd,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,  # mitigates shell injection risk
            text=True,  # returns stdout as str instead of bytes
            timeout=2,
        )
        self.std_out = result.stdout
        return result.stdout


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
    # args_ids: list = field(default_factory=list)  # creates new empty list

    @property
    def long_commands(self):
        return [self.base + sub for sub in self.subs]

    def __post_init__(self):
        self.io = {}
        for long_cmd in self.long_commands:
            input_output = InputOutput(long_cmd)
            self.io[input_output.args_id] = input_output
            setattr(self, input_output.args_id, input_output)

chezmoi = Chezmoi()
