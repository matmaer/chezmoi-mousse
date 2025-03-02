from dataclasses import dataclass, field

from chezmoi_mousse.commands import Utils

@dataclass
class InputOutput(Utils):
    long_command: list[str]
    arg_id: str
    std_out: str = ""
    py_out: str | list | dict = field(
        init=False, default="initial py_out value"
    )
    label: str = field(init=False, default="no label available")

    def update(self) -> str | list | dict:
        self.std_out = self.subprocess_run(self.long_command)
        self.py_out = self.parse_std_out(self.std_out)
        return self.py_out

    def __post_init__(self):
        self.label = " ".join(
            [w for w in self.long_command if not w.startswith("-")]
        )


class Chezmoi(Utils):

    name = "chezmoi"
    base = [name] + [
        "--no-pager",
        "--color=false",
        "--no-tty",
        "--progress=false",
    ]
    subs = [
        ["cat-config"],
        ["data", "--format=json"],
        ["doctor"],
        ["dump-config", "--format=json"],
        ["git", "log", "--", "--oneline"],
        ["git", "status"],
        ["ignored"],
        ["managed", "--path-style=absolute"],
        ["status", "--parent-dirs"],
        ["unmanaged", "--path-style=absolute"],
    ]

    @property
    def all_long_commands(self):
        return [self.base + sub for sub in self.subs]

    def __init__(self):
        for long_cmd in self.all_long_commands:
            arg_id = Utils.get_arg_id(long_command=long_cmd)
            setattr(self, arg_id, InputOutput(long_cmd, arg_id))


chezmoi = Chezmoi()
