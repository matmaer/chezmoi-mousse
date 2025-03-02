from dataclasses import dataclass, field

from chezmoi_mousse.commands import Utils

@dataclass
class InputOutput:
    long_command: list[str]
    arg_id: str
    std_out: str = ""
    py_out: str | list | dict = field(
        init=False, default="initial py_out value"
    )
    label: str = field(init=False, default="no label available")

    def update(self) -> str | list | dict:
        self.std_out = Utils.subprocess_run(self.long_command)
        self.py_out = Utils.parse_std_out(self.std_out)
        return self.py_out

    def __post_init__(self):
        self.label = " ".join(
            [w for w in self.long_command if not w.startswith("-")]
        )


class Chezmoi:

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

    def __init__(self):

        self.cmd_ids = {}  # should be dict with arg_id with sub dict of long_cmd and label

        for long_cmd in  [self.base + sub for sub in self.subs]:
            arg_id = Utils.get_arg_id(long_command=long_cmd)
            label = Utils.get_label(long_command=long_cmd)
            self.cmd_ids[arg_id] = {"long_cmd": long_cmd, "label": label}
            setattr(self, arg_id, InputOutput(long_cmd, arg_id))


chezmoi = Chezmoi()
