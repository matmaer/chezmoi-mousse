from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from textual.widgets import Link, ListItem, ListView, Static

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds


__all__ = ["PwMgrInfoList"]


class PwMgrInfo(Enum):
    @dataclass(slots=True)
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


class PwMgrInfoList(ListView):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.listview_id)

    def populate_listview(self, pw_mgr_commands: list[str]) -> None:
        for cmd in pw_mgr_commands:
            for pw_mgr in PwMgrInfo:
                if pw_mgr.value.doctor_check == cmd:
                    self.append(
                        ListItem(
                            Link(cmd, url=pw_mgr.value.link),
                            Static(pw_mgr.value.description),
                        )
                    )
                    break
