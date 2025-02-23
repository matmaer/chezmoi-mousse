# import json
import subprocess
from dataclasses import dataclass, field


@dataclass
class Command:
    id: str = field(init=False)
    label: str = field(init=False)
    std_out: str = field(init=False, default="nothing yet")
    long_command: list[str] = field(default_factory=list)

    def get(self, refresh: bool = False) -> str:
        if refresh or self.std_out == "nothing yet":
            result = subprocess.run(
                self.long_command,
                capture_output=True,
                check=True,  # raises exception for any non-zero return code
                shell=False,  # mitigates shell injection risk
                text=True,  # returns stdout as str instead of bytes
                timeout=2,
            )
            self.std_out = result.stdout
        return self.std_out

    def __post_init__(self):
        self.label = " ".join(
            [_ for _ in self.long_command[1:] if not _.startswith("-")]
        )
        self.id = self.label
        self.id = self.label.replace(" ", "_")
        self.id = self.id.replace("-", "_")


class Chezmoi:
    _base: list = [
        "chezmoi",
        "--no-pager",
        "--color=false",
        "--no-tty",
        "--progress=false",
    ]
    _subs: list[list] = [
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


    def __init__(self):
        for cmd in [self._base + sub for sub in self._subs]:
            command = Command(long_command=cmd)
            setattr(self, command.id, command)

chezmoi = Chezmoi()
