from dataclasses import dataclass, field
import json
import subprocess
import tomllib
import yaml

from textual.theme import Theme


SPLASH_7BIT = """\
 _______ _______ _______ _______ ____ ____ _______ _o_
|       |   |   |    ___|___    |    `    |       |   |
|    ---|       |     __|     __|         |   |   |   |
|       |   |   |       |       |   |`|   |       |   |
`-------^---^---^-------^-------^---' '---^-------^---'
   ____ ____ _______ ___ ___ _______ _______ _______
  |    `    |       |   |   |    ___|    ___|    ___|
  |         |   |   |   |   |__     |__     |     __|
  |   |`|   |       |       |       |       |       |
  '---' '---^-------^-------^-------^-------^-------'
""".splitlines()

SPLASH_8BIT = """\
 _______ _______ _______ _______ ____ ____ _______ _o_
|       |   |   |    ___|___    |    ˇ    |       |   |
|    ---|       |     __|     __|         |   |   |   |
|       |   |   |       |       |   |ˇ|   |       |   |
`-------^---^---^-------^-------^---' '---^-------^---'
   ____ ____ _______ ___ ___ _______ _______ _______
  |    ˇ    |       |   |   |    ___|    ___|    ___|
  |         |   |   |   |   |__     |__     |     __|
  |   |ˇ|   |       |       |       |       |       |
  '---' '---^-------^-------^-------^-------^-------'
""".splitlines()

SPLASH_ASCII_ART = """\
 _________________________________________________ _o_
|`      |   |   |    ___|___    |`   '    |       |   |
|    ===|       |     __|     __|         |   |   |   |
|       |   |   |       |       |   |ˇ|   |       |   |
`-------^---^---^-------^-------^---' '---^-------^---'
  ._________._______._______._______._______._______.
  |    '    |       |   |   |    ___|    ___|    ___|
  |         |   |   |   |   |__     |__     |     __|
  |   |ˇ|   |       |       |       |       |       |
  '---' '---^-------^-------^-------^-------^-------'
""".replace(
    "===", "=\u200b=\u200b="
).splitlines()

SPLASH = SPLASH_ASCII_ART

# # provisional diagrams until dynamically created
FLOW = """\
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│home directory│    │ working copy │    │  local repo  │    │ remote repo  │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │                   │
       │    chezmoi add    │                   │                   │
       │   chezmoi re-add  │                   │                   │
       │──────────────────>│                   │                   │
       │                   │                   │                   │
       │   chezmoi apply   │                   │                   │
       │<──────────────────│                   │                   │
       │                   │                   │                   │
       │  chezmoi status   │                   │                   │
       │   chezmoi diff    │                   │                   │
       │<─ ─ ─ ─ ─ ─ ─ ─ ─>│                   │     git push      │
       │                   │                   │──────────────────>│
       │                   │                   │                   │
       │                   │           chezmoi git pull            │
       │                   │<──────────────────────────────────────│
       │                   │                   │                   │
       │                   │    git commit     │                   │
       │                   │──────────────────>│                   │
       │                   │                   │                   │
       │                   │    autoCommit     │                   │
       │                   │──────────────────>│                   │
       │                   │                   │                   │
       │                   │                autoPush               │
       │                   │──────────────────────────────────────>│
       │                   │                   │                   │
       │                   │                   │                   │
┌──────┴───────┐    ┌──────┴───────┐    ┌──────┴───────┐    ┌──────┴───────┐
│ destination  │    │   staging    │    │   git repo   │    │  git remote  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
"""

BACKGROUND = "rgb(12, 14, 18)"

oled_dark_zen = Theme(
    name="oled-dark-zen",
    dark=True,
    luminosity_spread=0.9,
    text_alpha=0.9,
    accent="rgb(241, 135, 251)",
    background=BACKGROUND,
    error="rgb(203, 68, 31)",
    foreground="rgb(234, 232, 227)",
    panel="rgb(98, 118, 147)",
    primary="rgb(67, 156, 251)",
    secondary="rgb(37, 146, 137)",
    success="rgb(63, 170, 77)",
    surface="rgb(24, 28, 34)",
    warning="rgb(224, 195, 30)",
    variables={
        "footer-background": BACKGROUND,
        "footer-description-background": BACKGROUND,
        "footer-item-background": BACKGROUND,
        "footer-key-background": BACKGROUND,
        "link-background": BACKGROUND,
        "scrollbar-corner-color": BACKGROUND,
    },
)


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
