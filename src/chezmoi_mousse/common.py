"""Modules for singletons or any other shared resources."""

import json
from pathlib import Path
import subprocess
from dataclasses import dataclass

from textual.theme import Theme


@dataclass
class InputOutput:

    long_command: list[str]
    std_out: str = ""

    @property
    def label(self):
        return " ".join([w for w in self.long_command if not w.startswith("-")])

    def update(self) -> None:
        result = subprocess.run(
            self.long_command,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,
            text=True,  # returns stdout as str instead of bytes
            timeout=2,
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
    dest_dir_path: Path | None = None

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
        "git_status": ["git", "status"],
        "ignored": ["ignored"],
        "managed": [
            "managed",
            "--path-style=absolute",
            "--include=dirs,files",
        ],
        "chezmoi_status": ["status", "--parent-dirs"],
        "unmanaged": ["unmanaged", "--path-style=absolute"],
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
    def get_doctor_list(self) -> list[str]:
        return self.doctor.std_out.splitlines()

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


chezmoi = Chezmoi()


BACKGROUND = "rgb(12, 14, 18)"

mousse_theme = Theme(
    name="mousse-theme",
    dark=True,
    accent="rgb(241, 135, 251)",  # custom #F187FB
    background=BACKGROUND,
    error="#ba3c5b",  # textual dark
    foreground="rgb(222, 218, 209)",  # custom #DEDAE1
    primary="#0178D4",  # textual dark
    secondary="#004578",  # textual dark
    success="#4EBF71",  # textual dark
    warning="#ffa62b",  # textual dark
    variables={
        "footer-background": BACKGROUND,
        "footer-description-background": BACKGROUND,
        "footer-item-background": BACKGROUND,
        "footer-key-background": BACKGROUND,
        "link-background": BACKGROUND,
        "scrollbar-corner-color": BACKGROUND,
    },
)

# pylint: disable=line-too-long
integrated_command_map = {
    "age": {
        "Description": "A simple, modern and secure file encryption tool",
        "URL": "https://github.com/FiloSottile/age",
    },
    "gopass": {
        "Description": "The slightly more awesome standard unix password manager for teams.",
        "URL": "https://github.com/gopasspw/gopass",
    },
    "pass": {
        "Description": "Stores, retrieves, generates, and synchronizes passwords securely",
        "URL": "https://www.passwordstore.org/",
    },
    "rbw": {
        "Description": "Unofficial Bitwarden CLI",
        "URL": "https://git.tozt.net/rbw",
    },
    "vault": {
        "Description": "A tool for managing secrets",
        "URL": "https://vaultproject.io/",
    },
    "pinentry": {
        "Description": "Collection of simple PIN or passphrase entry dialogs which utilize the Assuan protocol",
        "URL": "https://gnupg.org/related_software/pinentry/",
    },
    "keepassxc": {
        "Description": "Cross-platform community-driven port of Keepass password manager",
        "URL": "https://keepassxc.org/",
    },
}

# Chezmoi status command output reference:
# https://www.chezmoi.io/reference/commands/status/
chezmoi_status_map = {
    " ": {
        "Status": "No change",
        "Re_Add_Change": "No change",
        "Apply_Change": "No change",
    },
    "A": {
        "Status": "Added",
        "Re_Add_Change": "Entry was created",
        "Apply_Change": "Entry will be created",
    },
    "D": {
        "Status": "Deleted",
        "Re_Add_Change": "Entry was deleted",
        "Apply_Change": "Entry will be deleted",
    },
    "M": {
        "Status": "Modified",
        "Re_Add_Change": "Entry was modified",
        "Apply_Change": "Entry will be modified",
    },
    "R": {
        "Status": "Run",
        "Re_Add_Change": "Not applicable",
        "Apply_Change": "Script will be run",
    },
}

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
