from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalGroup
from textual.widgets import Label, Link, Static

from chezmoi_mousse import AppType, Chars, CommandResult, SectionLabels, Tcss

from .custom_collapsible import CustomCollapsible

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds


__all__ = ["PwMgrInfoView"]


class InfoStrings(StrEnum):
    additional_info_label = "Additional Info"
    confusing = "Check your package manager which implementation is used as there are confusingly similar named packages."
    fully_open_source = "Fully open source and auditable worldwide. No third party trust required. But beware of your supply chain: package manager, certificate authority, maintainers reputation, etc."
    info_warning = f"[$text-warning]{Chars.warning_sign} The additional info is provided but may not be up-to-date or correct. Please contribute to improve it.{Chars.warning_sign}[/]"
    not_documented = "Not yet documented in chezmoi mousse."
    not_open_source = "Not open source, cannot be audited but it's ok if you trust this third party to handle your secrets securely and cannot access them."
    source_available = "The code is publicly available. No third party trust required. But beware of your supply chain: package manager, certificate authority, maintainers reputation and so on."


@dataclass(slots=True)
class PwMgrData:
    description: str
    doctor_check: str
    link: str
    doctor_status: str = "unknown"
    info: str = ""


class PwMgrInfo(Enum):
    age_command = PwMgrData(
        doctor_check="age-command",
        description="A simple, modern and secure file encryption tool.",
        link="https://github.com/FiloSottile/age",
        info=InfoStrings.fully_open_source,
    )
    bitwarden_command = PwMgrData(
        doctor_check="bitwarden-command",
        description="Bitwarden Password Manager",
        link="https://github.com/bitwarden",
        info=InfoStrings.source_available,
    )
    bitwarden_secrets_command = PwMgrData(
        doctor_check="bitwarden-secrets-command",
        description="Bitwarden Secrets Manager CLI for managing secrets securely.",
        link="https://github.com/bitwarden",
        info=InfoStrings.fully_open_source,
    )
    dashlane_command = PwMgrData(
        doctor_check="dashlane-command",
        description="Simple and secure access to all your online accounts. At work, home, and everywhere in between.",
        link="https://github.com/dashlane",
        info=InfoStrings.not_open_source,
    )
    doppler_command = PwMgrData(
        doctor_check="doppler-command",
        description="Doppler is the multi-cloud SecretOps Platform developers and security teams trust to provide secrets management at enterprise scale.",
        link="https://github.com/dopplerhq",
        info=InfoStrings.not_open_source,
    )
    gopass_command = PwMgrData(
        doctor_check="gopass-command",
        description="The slightly more awesome standard unix password manager for teams.",
        link="https://github.com/gopasspw/gopass",
        info=InfoStrings.fully_open_source,
    )
    keeper_command = PwMgrData(
        doctor_check="keeper-command",
        description="An interface to Keeper Password Manager",
        link="https://github.com/Keeper-Security/Commander",
        info=InfoStrings.not_open_source,
    )
    keepassxc_command = PwMgrData(
        doctor_check="keepassxc-command",
        description="Cross-platform community-driven port of Keepass password manager.",
        link="https://keepassxc.org/",
        info=InfoStrings.fully_open_source,
    )
    lastpass_command = PwMgrData(
        doctor_check="lastpass-command",
        description="Old LastPass CLI for accessing your LastPass vault.",
        link="https://https://github.com/lastpass",
        info=InfoStrings.not_open_source,
    )
    one_password_command = PwMgrData(
        doctor_check="one-password-command",
        description="Secure all sign-ins to every application from any device.",
        link="https://github.com/1Password/for-open-source",
        info=InfoStrings.not_open_source,
    )
    pass_command = PwMgrData(
        doctor_check="pass-command",
        description="Stores, retrieves, generates, and synchronizes passwords securely.",
        link="https://www.passwordstore.org/",
        info=InfoStrings.confusing,
    )
    passhole_command = PwMgrData(
        doctor_check="passhole-command",
        description="A secure hole for your passwords (KeePass CLI).",
        link="https://github.com/Evidlo/passhole",
        info=InfoStrings.not_open_source,
    )
    pinentry_command = PwMgrData(
        doctor_check="pinentry-command",
        description="Collection of simple PIN or passphrase entry dialogs which utilize the Assuan protocol.",
        link="https://gnupg.org/related_software/pinentry/",
        info=InfoStrings.fully_open_source,
    )
    rbw_command = PwMgrData(
        doctor_check="rbw-command",
        description="Unofficial Bitwarden.",
        link="https://git.tozt.net/rbw",
        info=InfoStrings.not_documented,
    )
    vault_command = PwMgrData(
        doctor_check="vault-command",
        description="A tool for managing secrets.",
        link="https://vaultproject.io/",
        info=InfoStrings.not_documented,
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

        super().__init__(
            VerticalGroup(
                Label(
                    SectionLabels.project_link, classes=Tcss.sub_section_label
                ),
                Link(self.stripped_link, url=self.pw_mgr_data.link),
                Label(
                    SectionLabels.project_description,
                    classes=Tcss.sub_section_label,
                ),
                Static(self.pw_mgr_data.description, markup=False),
                Label(
                    InfoStrings.additional_info_label,
                    classes=Tcss.sub_section_label,
                ),
                Static(self.pw_mgr_data.info, markup=False),
                classes=Tcss.pw_mgr_group,
            ),
            title=(
                f"[$text-primary]Doctor check: "
                f"{self.pw_mgr_data.doctor_check}[/]"
            ),
        )


class PwMgrInfoView(Vertical):

    def __init__(self, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.view.pw_mgr_info)

    def compose(self) -> ComposeResult:
        yield Label(
            SectionLabels.password_managers, classes=Tcss.main_section_label
        )

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

        self.mount(Static(f"\n{InfoStrings.info_warning}"))
