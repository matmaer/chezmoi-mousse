import json
import subprocess
import tomllib

# from textual.reactive import reactive
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


# @dataclass
class InputOutput:

    def __init__(self, long_command: list[str] | None = None) -> None:
        self.std_out = "will hold std_out"
        self.long_command = long_command

    @property
    def py_out(self):
        std_out = self.std_out.strip()
        to_return = "should hold parsed std_out"

        if std_out == "":
            to_return = "std_out is an empty string"
        if std_out == "will hold std_out":
            to_return = "no std_out available to parse"
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
        return to_return

    @property
    def label(self):
        return " ".join(
            [w for w in self.long_command if not w.startswith("-")]
        )

    # don't call subprocess_run with self.long_command, so we can use this
    # method to update the std_out attribute of any instance without the
    # long_command attribute being set.

    def _update(self) -> None:
        """Re-run the subprocess call, don't return anything."""
        result = _subprocess_run(self.long_command)
        self.std_out = result

    def updated_std_out(self) -> str:
        """Re-run subprocess call and return std_out."""
        self._update()
        return self.std_out

    def updated_py_out(self) -> str | list | dict:
        """Re-run subprocess call and return py_out."""
        self._update()
        return self.py_out

    # run a command and update the class instance without returning anything
    def run(self, long_command) -> str:
        self.long_command = long_command
        self._update()


class Chezmoi:
    # pylint: disable=too-few-public-methods
    # the reason for a class is easy dot notation access to all the commands

    # don't create this dynamically, hard on linters, type checking and
    # exceptions show up much later than they should.
    cat_config = InputOutput()
    template_data = InputOutput()
    doctor = InputOutput()
    dump_config = InputOutput()
    git_log = InputOutput()
    git_status = InputOutput()
    ignored = InputOutput()
    managed = InputOutput()
    status = InputOutput()
    unmanaged = InputOutput()

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
        "status": ["status", "--parent-dirs"],
        "unmanaged": ["unmanaged", "--path-style=absolute"],
    }

    long_commands = {}

    def __init__(self) -> None:

        # Populate all InputOutput instances with the corresponding
        # long_command, this way of looping also makes sure the arg_id matches
        # the attribute name. If not, an exception will be raised by getattr.
        for arg_id, sub_cmd in self.subs.items():
            # using getattr to set the attribute in one lines
            getattr(self, arg_id).long_command = self.base + sub_cmd
            # Used for easy looping. Looping over just the arg_id attributes
            # would require filtering out attributes, also keeps the arg_id
            # and sub_cmd/attribute name in sync.
            self.long_commands[arg_id] = self.base + sub_cmd
