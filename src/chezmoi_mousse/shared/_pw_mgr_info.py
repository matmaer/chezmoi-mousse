"""Shared between MainScreen (config tab) and the InitScreen."""

from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalGroup
from textual.widgets import Link, Static

from chezmoi_mousse import AppType, Chars, CommandResult, Tcss, ViewName

from ._custom_collapsible import CustomCollapsible
from ._section_headers import SectionLabel, SectionLabelText

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds


__all__ = ["PwMgrInfoView"]


class DoctorChecks(Enum):
    age_command = "age-command"
    bitwarden_command = "bitwarden-command"
    bitwarden_secrets_command = "bitwarden-secrets-command"
    dashlane_command = "dashlane-command"
    doppler_command = "doppler-command"
    gopass_command = "gopass-command"
    keepassxc_command = "keepassxc-command"
    keeper_command = "keeper-command"
    lastpass_command = "lastpass-command"
    one_password_command = "1password-command"
    pass_command = "pass-command"
    passhole_command = "passhole-command"
    pinentry_command = "pinentry-command"
    rbw_command = "rbw-command"
    vault_command = "vault-command"


class AdditionalInfo(StrEnum):
    confusing = "Check your package manager which implementation is used as there are confusingly similar named packages."
    fully_open_source = "Fully open source and auditable worldwide. No third party trust required. But beware of your supply chain: package manager, certificate authority, maintainers reputation, etc."
    source_available = "The code is publicly available. No third party trust required. But beware of your supply chain: package manager, certificate authority, maintainers reputation and so on."
    not_open_source = "Not open source, cannot be audited but it's ok if you trust this third party to handle your secrets securely and cannot access them."
    not_documented = "Not yet documented in chezmoi mousse."
    additional_info_warning = f"{Chars.warning_sign} The additional info is provided but may not be up-to-date or correct. Please contribute to improve it."


@dataclass(slots=True)
class PwMgrData:
    description: str
    doctor_check: str
    link: str
    doctor_status: str = "unknown"
    info: str = ""


class PwMgrInfo(Enum):
    age_command = PwMgrData(
        doctor_check=DoctorChecks.age_command.value,
        description="A simple, modern and secure file encryption tool.",
        link="https://github.com/FiloSottile/age",
        info=AdditionalInfo.fully_open_source,
    )
    bitwarden_command = PwMgrData(
        doctor_check=DoctorChecks.bitwarden_command.value,
        description="Bitwarden Password Manager",
        link="https://github.com/bitwarden",
        info=AdditionalInfo.source_available,
    )
    bitwarden_secrets_command = PwMgrData(
        doctor_check=DoctorChecks.bitwarden_secrets_command.value,
        description="Bitwarden Secrets Manager CLI for managing secrets securely.",
        link="https://github.com/bitwarden",
        info=AdditionalInfo.fully_open_source,
    )
    dashlane_command = PwMgrData(
        doctor_check=DoctorChecks.dashlane_command.value,
        description="Simple and secure access to all your online accounts. At work, home, and everywhere in between.",
        link="https://github.com/dashlane",
        info=AdditionalInfo.not_open_source,
    )
    doppler_command = PwMgrData(
        doctor_check=DoctorChecks.doppler_command.value,
        description="Doppler is the multi-cloud SecretOps Platform developers and security teams trust to provide secrets management at enterprise scale.",
        link="https://github.com/dopplerhq",
        info=AdditionalInfo.not_open_source,
    )
    gopass_command = PwMgrData(
        doctor_check=DoctorChecks.gopass_command.value,
        description="The slightly more awesome standard unix password manager for teams.",
        link="https://github.com/gopasspw/gopass",
        info=AdditionalInfo.fully_open_source,
    )
    keeper_command = PwMgrData(
        doctor_check=DoctorChecks.keeper_command.value,
        description="An interface to Keeper Password Manager",
        link="https://github.com/Keeper-Security/Commander",
        info=AdditionalInfo.not_open_source,
    )
    keepassxc_command = PwMgrData(
        doctor_check=DoctorChecks.keepassxc_command.value,
        description="Cross-platform community-driven port of Keepass password manager.",
        link="https://keepassxc.org/",
        info=AdditionalInfo.fully_open_source,
    )
    lastpass_command = PwMgrData(
        doctor_check=DoctorChecks.lastpass_command.value,
        description="Old LastPass CLI for accessing your LastPass vault.",
        link="https://https://github.com/lastpass",
        info=AdditionalInfo.not_open_source,
    )
    one_password_command = PwMgrData(
        doctor_check=DoctorChecks.one_password_command.value,
        description="Secure all sign-ins to every application from any device.",
        link="https://github.com/1Password/for-open-source",
        info=AdditionalInfo.not_open_source,
    )
    pass_command = PwMgrData(
        doctor_check=DoctorChecks.pass_command.value,
        description="Stores, retrieves, generates, and synchronizes passwords securely.",
        link="https://www.passwordstore.org/",
        info=AdditionalInfo.confusing,
    )
    passhole_command = PwMgrData(
        doctor_check=DoctorChecks.passhole_command.value,
        description="A secure hole for your passwords (KeePass CLI).",
        link="https://github.com/Evidlo/passhole",
        info=AdditionalInfo.not_open_source,
    )
    pinentry_command = PwMgrData(
        doctor_check=DoctorChecks.pinentry_command.value,
        description="Collection of simple PIN or passphrase entry dialogs which utilize the Assuan protocol.",
        link="https://gnupg.org/related_software/pinentry/",
        info=AdditionalInfo.fully_open_source,
    )
    rbw_command = PwMgrData(
        doctor_check=DoctorChecks.rbw_command.value,
        description="Unofficial Bitwarden.",
        link="https://git.tozt.net/rbw",
        info=AdditionalInfo.not_documented,
    )
    vault_command = PwMgrData(
        doctor_check=DoctorChecks.vault_command.value,
        description="A tool for managing secrets.",
        link="https://vaultproject.io/",
        info=AdditionalInfo.not_documented,
    )

    @classmethod
    def all_pw_mgr_commands(cls) -> list[str]:
        return [pw_mgr.value.doctor_check for pw_mgr in cls]

    @classmethod
    def get_member_from_doctor_check(cls, doctor_check: str) -> PwMgrData:
        for member in PwMgrInfo:
            if member.value.doctor_check == doctor_check:
                return member.value
        raise ValueError(
            f"No PwMgrInfo member for doctor_check '{doctor_check}'"
        )


class PwCollapsible(CustomCollapsible, AppType):

    def __init__(self, pw_mgr_data: PwMgrData) -> None:
        self.pw_mgr_data = pw_mgr_data
        self.stripped_link = self.pw_mgr_data.link.replace(
            "https://", ""
        ).replace("www.", "")
        self.collapsible_title = (
            f"Doctor check: {self.pw_mgr_data.doctor_check}"
        )

        super().__init__(
            VerticalGroup(
                Link(self.stripped_link, url=self.pw_mgr_data.link),
                Static(self.pw_mgr_data.description, markup=False),
                Static(self.pw_mgr_data.info, markup=False),
                classes=Tcss.pw_mgr_group.name,
            ),
            title=self.collapsible_title,
        )

    def on_mount(self) -> None:
        collapsible_title = self.query_exactly_one("CollapsibleTitle")
        collapsible_title.styles.color = self.app.theme_variables[
            "primary-lighten-3"
        ]


class PwMgrInfoView(Vertical):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.view_id(view=ViewName.pw_mgr_info_view))

    def compose(self) -> ComposeResult:
        yield SectionLabel(SectionLabelText.password_managers)

    def populate_pw_mgr_info(self, doctor_results: "CommandResult") -> None:
        doctor_lines = doctor_results.std_out.splitlines()
        pw_mgr_data_list: list[PwMgrData] = []

        for line in doctor_lines[1:]:  # Skip header line
            row = tuple(line.split(maxsplit=2))
            if row[1] not in PwMgrInfo.all_pw_mgr_commands():
                continue
            pw_mgr_data = PwMgrInfo.get_member_from_doctor_check(row[1])
            pw_mgr_data_list.append(pw_mgr_data)

        for item in pw_mgr_data_list:
            pw_collapsible = PwCollapsible(pw_mgr_data=item)
            self.mount(pw_collapsible)
