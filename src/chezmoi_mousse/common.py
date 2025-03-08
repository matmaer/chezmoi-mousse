import json
import subprocess
import tomllib
from dataclasses import dataclass

from textual.theme import Theme


def _subprocess_run(long_command: list[str] | None = None) -> str:
    result = subprocess.run(
        long_command,
        capture_output=True,
        check=True,  # raises exception for any non-zero return code
        shell=False,  # mitigates shell injection risk
        text=True,  # returns stdout as str instead of bytes
        timeout=2,
    )
    return result.stdout


@dataclass
class InputOutput:

    long_command: list[str]
    std_out: str = ""

    @property
    def py_out(self):

        if self.std_out == "":
            return "no std_out available to parse"

        std_out = self.std_out.strip()
        to_return = "should hold parsed std_out"

        try:
            return json.loads(std_out)
        except json.JSONDecodeError:
            try:
                return tomllib.loads(std_out)
            except tomllib.TOMLDecodeError:
                pass
            # not don't attempt to parse yaml, as it will parse a single string
        if std_out.count("\n") > 0:
            to_return = std_out.splitlines()
        else:
            to_return = std_out
        return to_return

    @property
    def label(self):
        return " ".join(
            [w for w in self.long_command if not w.startswith("-")]
        )

    def update(self) -> None:
        """(Re)run the subprocess call, don't return anything."""
        result = _subprocess_run(self.long_command)
        self.std_out = result

    def updated_std_out(self) -> str:
        """Re-run subprocess call and return std_out."""
        self.update()
        return self.std_out

    def updated_py_out(self) -> str | list | dict:
        """Re-run subprocess call and return py_out."""
        self.update()
        return self.py_out


class Chezmoi:

    cat_config: type[InputOutput]
    chezmoi_status: type[InputOutput]
    doctor: type[InputOutput]
    dump_config: type[InputOutput]
    git_log: type[InputOutput]
    git_status: type[InputOutput]
    ignored: type[InputOutput]
    managed: type[InputOutput]
    template_data: type[InputOutput]
    unmanaged: type[InputOutput]
    dest_dir: str  # shortcut for "destDir" config value access

    base = [
        "chezmoi",
        "--no-pager",
        "--color=false",
        "--no-tty",
        "--progress=false",
    ]

    subs = {
        "cat_config": ["cat-config"],
        "template_data": ["data", "--format=json"],
        "doctor": ["doctor"],
        "dump_config": ["dump-config", "--format=json"],
        "git_log": ["git", "log", "--", "--oneline"],
        "git_status": ["git", "status"],
        "ignored": ["ignored"],
        "managed": ["managed", "--path-style=absolute"],
        "chezmoi_status": ["status", "--parent-dirs"],
        "unmanaged": ["unmanaged", "--path-style=absolute"],
    }

    dest_dir: str

    def __init__(self) -> None:

        self.long_commands = {}

        for arg_id, sub_cmd in self.subs.items():
            long_cmd = self.base + sub_cmd
            NewClass = type(arg_id, (InputOutput,), {})
            setattr(
                self,
                arg_id,
                NewClass(
                    long_command=long_cmd,
                ),
            )
            # TODO: remove after testing
            # if arg_id == "dump_config":
            #     setattr(self, "dest_dir", self.dump_config.update())
            # map arg_id to the long_command, for looping in LoadingScreen
            self.long_commands[arg_id] = long_cmd


# there must be a better way to do this
chezmoi = Chezmoi()


SPLASH_7BIT = """\
 _______ _______ _______ _______ ____ ____ _______ _._
|       |   |   |    ___|___    |    '    |       |   |
|    ---|       |     __|     __|         |   |   |   |
|       |   |   |       |       |   |`|   |       |   |
`-------^---^---^-------^-------^---' '---^-------^---'
   ____ ____ _______ ___ ___ _______ _______ _______
  |    '    |       |   |   |    ___|    ___|    ___|
  |         |   |   |   |   |__     |__     |     __|
  |   |`|   |       |       |       |       |       |
  '---' '---^-------^-------^-------^-------^-------'
""".splitlines()

SPLASH_8BIT = """\
 _______ _______ _______ _______ ____ ____ _______ _._
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
 _______________________________ _________________ _o_
|       |   |   |    ___|___    |    '    |       |   |
|    ===|       |     __|     __|         |   |   |   |
|       |   |   |       |       |   |ˇ|   |       |   |
`-------^---^---^-------^-------^---' '---^-------^---'
   _________________________________________________
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
    accent="rgb(241, 135, 251)",  # #F187FB
    background=BACKGROUND,
    error="rgb(203, 68, 31)",  # #CB441F
    foreground="rgb(222, 218, 209)",  # #DEDAE1
    panel="rgb(98, 118, 147)",  # #627693
    primary="rgb(67, 156, 251)",  # #439CFB
    success="rgb(63, 170, 77)",  # #3FAA4D
    warning="rgb(224, 195, 30)",  # #E0C31E
    variables={
        "footer-background": BACKGROUND,
        "footer-description-background": BACKGROUND,
        "footer-item-background": BACKGROUND,
        "footer-key-background": BACKGROUND,
        "link-background": BACKGROUND,
        "scrollbar-corner-color": BACKGROUND,
    },
)


oled_dark_zen_v2 = Theme(
    name="oled-dark-zen-v2",
    dark=True,
    luminosity_spread=0.9,
    text_alpha=0.9,
    accent="rgb(255, 95, 184)",  # #FF5FB8
    background=BACKGROUND,
    error="rgb(197, 0, 113)",  # #C50071
    foreground="rgb(222, 218, 209)",  # #DEDAE1
    panel="rgb(98, 118, 147)",  # #627693
    primary="rgb(147, 156, 255)",  # #939CFF
    secondary="rgb(0, 197, 84)",  # #00C554
    success="rgb(0, 203, 158)",  # #00CB9E
    warning="rgb(144, 185, 0)",  # #90B900
    variables={
        "footer-background": BACKGROUND,
        "footer-description-background": BACKGROUND,
        "footer-item-background": BACKGROUND,
        "footer-key-background": BACKGROUND,
        "link-background": BACKGROUND,
        "scrollbar-corner-color": BACKGROUND,
    },
)
