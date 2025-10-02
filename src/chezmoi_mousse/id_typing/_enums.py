from dataclasses import dataclass
from enum import Enum

from chezmoi_mousse.id_typing._str_enums import Chars

__all__ = ["OperateHelp", "PwMgrInfo", "Switches"]


class OperateHelp(Enum):
    add = "[$text-primary]Path will be added to your chezmoi dotfile manager source state.[/]"
    apply = "[$text-primary]Local file (target state) in the destination directory will be modified.[/]"
    auto_commit = f"[$text-warning]{Chars.warning_sign} Auto commit is enabled: files will also be committed.{Chars.warning_sign}[/]"
    autopush = f"[$text-warning]{Chars.warning_sign} Auto push is enabled: files will be pushed to the remote.{Chars.warning_sign}[/]"
    changes_mode_disabled = (
        "Changes mode disabled, operations will dry-run only"
    )
    changes_mode_enabled = "Changes mode enabled, operations will run."
    destroy = (
        "[$text-primary]Remove target from the source state, the destination directory, and the state.[/]",
        "[$text-error]The destroy command permanently removes files both from your home directory and chezmoi's source directory, make sure you have a backup![/]",
    )
    diff_color = (
        "[$text-success]+ green lines will be added[/]",
        "[$text-error]- red lines will be removed[/]",
        f"[dim]{Chars.bullet} dimmed lines for context[/]",
    )
    forget = "[$text-primary]Remove targets from the source state, i.e. stop managing them.[/]"
    re_add = (
        "[$text-primary]Overwrite the source state with current local file[/]"
    )


class PwMgrInfo(Enum):
    @dataclass
    class PwMgrData:
        doctor_check: str
        description: str
        link: str

    age_command = PwMgrData(
        doctor_check="age-command",
        description="A simple, modern and secure file encryption tool",
        link="https://github.com/FiloSottile/age",
    )
    bitwarden_command = PwMgrData(
        doctor_check="bitwarden-command",
        description="Bitwarden Password Manager",
        link="https://github.com/bitwarden/cli",
    )
    bitwarden_secrets_command = PwMgrData(
        doctor_check="bitwarden-secrets-command",
        description="Bitwarden Secrets Manager CLI for managing secrets securely.",
        link="https://github.com/bitwarden/bitwarden-secrets",
    )
    doppler_command = PwMgrData(
        doctor_check="doppler-command",
        description="The Doppler CLI for managing secrets, configs, and environment variables.",
        link="https://github.com/DopplerHQ/cli",
    )
    gopass_command = PwMgrData(
        doctor_check="gopass-command",
        description="The slightly more awesome standard unix password manager for teams.",
        link="https://github.com/gopasspw/gopass",
    )
    keeper_command = PwMgrData(
        doctor_check="keeper-command",
        description="An interface to Keeper® Password Manager",
        link="https://github.com/Keeper-Security/Commander",
    )
    keepassxc_command = PwMgrData(
        doctor_check="keepassxc-command",
        description="Cross-platform community-driven port of Keepass password manager",
        link="https://keepassxc.org/",
    )
    lpass_command = PwMgrData(
        doctor_check="lpass-command",
        description="Old LastPass CLI for accessing your LastPass vault.",
        link="https://github.com/lastpass/lastpass-cli",
    )
    pass_command = PwMgrData(
        doctor_check="pass-command",
        description="Stores, retrieves, generates, and synchronizes passwords securely",
        link="https://www.passwordstore.org/",
    )
    pinentry_command = PwMgrData(
        doctor_check="pinentry-command",
        description="Collection of simple PIN or passphrase entry dialogs which utilize the Assuan protocol",
        link="https://gnupg.org/related_software/pinentry/",
    )
    rbw_command = PwMgrData(
        doctor_check="rbw-command",
        description="Unofficial Bitwarden CLI",
        link="https://git.tozt.net/rbw",
    )
    vault_command = PwMgrData(
        doctor_check="vault-command",
        description="A tool for managing secrets",
        link="https://vaultproject.io/",
    )


class Switches(Enum):
    @dataclass(frozen=True)
    class SwitchData:
        label: str
        tooltip: str

    expand_all = SwitchData(
        "expand all dirs",
        "Expand all managed directories. Depending on the unchanged switch.",
    )
    unchanged = SwitchData(
        "show unchanged files",
        "Include files unchanged files which are not found in the 'chezmoi status' output.",
    )
    unmanaged_dirs = SwitchData(
        "show unmanaged dirs",
        "The default (disabled), only shows directories which already contain managed files. This allows spotting new unmanaged files in already managed directories. Enable to show all directories which contain unmanaged files.",
    )
    unwanted = SwitchData(
        "show unwanted paths",
        "Include files and directories considered as 'unwanted' for a dotfile manager. These include cache, temporary, trash (recycle bin) and other similar files or directories. For example enable this to add files to your repository which are in a directory named '.cache'.",
    )
