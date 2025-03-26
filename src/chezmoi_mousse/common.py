import json
from pathlib import Path
import subprocess
from dataclasses import dataclass

from textual.theme import Theme


@dataclass
class StatusData:

    for_fs: bool
    status_code: str = "space"
    fs_change: str | None = None
    repo_change: str | None = None
    fs_path: Path | None = None

    # Chezmoi status command output reference:
    # https://www.chezmoi.io/reference/commands/status/

    @property
    def name(self):
        status_names = {
            "space": "No change",
            "A": "Added",
            "D": "Deleted",
            "M": "Modified",
            "R": "Modified Script",
        }
        return status_names[self.status_code]

    @property
    def change(self):
        if not self.for_fs:
            status_change = {
                "space": "no changes for repository",
                "A": "add to repository",
                "D": "mark as deleted in repository",
                "M": "modify in repository",
                "R": "not applicable for repository",
            }
        else:
            status_change = {
                "space": "no changes for filesystem",
                "A": "create on filesystem",
                "D": "delete from filesystem",
                "M": "modify on filesystem",
                "R": "modify script on filesystem",
            }
        return status_change[self.status_code]


@dataclass
class InputOutput:

    long_command: list[str]
    std_out: str = ""

    @property
    def label(self):
        return " ".join(
            [w for w in self.long_command if not w.startswith("-")]
        )

    def update(self) -> None:
        result = subprocess.run(
            self.long_command,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,
            text=True,  # returns stdout as str instead of bytes
            timeout=1,
        )
        self.std_out = result.stdout


class Chezmoi:

    cat_config: InputOutput
    chezmoi_status: InputOutput
    doctor: InputOutput
    dump_config: InputOutput
    git_log: InputOutput
    git_status: InputOutput
    ignored: InputOutput
    managed: InputOutput
    template_data: InputOutput
    unmanaged: InputOutput

    base = [
        "chezmoi",
        "--no-pager",
        "--color=off",
        "--no-tty",
        "--mode=file",
        # TODO "--force",  make changes without prompting: flag is not
        # compatible with "--interactive", find way to handle this.
        # "--force",
    ]

    # The reference with regards to --include and --exclued flags is here:
    # https://www.chezmoi.io/reference/command-line-flags/common/#available-entry-types
    # Currently starting out with support for types file and dir.
    subs = {
        "cat_config": ["cat-config"],
        "template_data": ["data", "--format=json"],
        "doctor": ["doctor"],
        "dump_config": ["dump-config", "--format=json"],
        # git is not an independent git command, it's ran by chezmoi because
        # it would otherwise only work if pwd is in the chezmoi git repo
        "git_log": [
            "git",
            "log",
            "--",
            "-10",
            "--no-color",
            "--no-decorate",
            "--date-order",
            "--no-expand-tabs",
            "--format=%ar by %cn; %s",
        ],
        # see remark above the git_log command, same applies
        # another advantage is that chezmoi will return the git status for
        # all files in the chezmoi repo, regardless of the current working
        # directory
        "git_status": ["git", "status"],
        "ignored": ["ignored"],
        "managed": [
            "managed",
            "--path-style=absolute",
            "--include=dirs,files",
        ],
        "unmanaged": ["unmanaged", "--path-style=absolute"],
        "chezmoi_status": ["status", "--parent-dirs", "--include=dirs,files"],
    }

    def __init__(self) -> None:

        self.long_commands = {}

        for arg_id, sub_cmd in self.subs.items():
            long_cmd = self.base + sub_cmd
            self.long_commands[arg_id] = long_cmd
            setattr(
                self,
                arg_id,
                InputOutput(long_cmd),
            )

    @property
    def get_config_dump(self) -> dict:
        command_output = getattr(self.dump_config, "std_out", "{}")
        return json.loads(command_output)

    @property
    def get_managed_paths(self) -> list[Path]:
        return sorted([Path(p) for p in self.managed.std_out.splitlines()])

    @property
    def get_unmanaged_paths(self) -> list[Path]:
        return sorted([Path(p) for p in self.unmanaged.std_out.splitlines()])

    @property
    def get_template_data(self) -> dict:
        command_output = getattr(self.template_data, "std_out", "{}")
        return json.loads(command_output)

    @property
    def get_doctor_rows(self) -> list[str]:
        return self.doctor.std_out.splitlines()


chezmoi = Chezmoi()

mousse_theme = Theme(
    name="mousse-theme",
    dark=True,
    accent="#F187FB",  # bespoke
    background="#000000",
    error="#ba3c5b",  # textual dark
    foreground="#DEDAE1",  # bespoke
    primary="#0178D4",  # textual dark
    secondary="#004578",  # textual dark
    success="#4EBF71",  # textual dark
    warning="#ffa62b",  # textual dark
)


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

# provisional diagrams until dynamically created
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
