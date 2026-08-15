from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from rich.text import Text
from textual import getters, work
from textual.containers import VerticalGroup
from textual.widgets import Collapsible, DataTable, Label, Link, Static

from chezmoi_mousse.named_tuples import PwMgrData
from chezmoi_mousse.str_enums import Chars, ColorVar, PwMgrStrings, SectionLabel, Tcss

if TYPE_CHECKING:
    from chezmoi_mousse.gui.textual_app import ChezmoiGui


__all__ = ["DoctorTable", "PwMgrInfo", "PwCollapsible"]


class DoctorTable(DataTable[Text]):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(self) -> None:
        super().__init__(cursor_type="row", show_cursor=False)

    def on_mount(self) -> None:
        self.row_color = {
            "ok": self.app.get_color(ColorVar.text_success),
            "info": self.app.get_color(ColorVar.info),
            "warning": self.app.get_color(ColorVar.text_warning),
            "failed": self.app.get_color(ColorVar.text_error),
            "error": self.app.get_color(ColorVar.text_error),
        }

    @work
    async def populate_table(self, doctor_lines: list[str]) -> None:
        doctor_lines = self.app.cmattr.cmd_results.doctor.std_out.splitlines()
        if not doctor_lines:
            self.notify("No doctor output available to display.")
            return
        self.add_columns(*doctor_lines[0].split())

        for line in doctor_lines[1:]:
            row = tuple(line.split(maxsplit=2))
            if row[0] == "info" and "not found in $PATH" in row[2]:
                new_row = [
                    Text(cell_text, style=self.row_color["info"]) for cell_text in row
                ]
                self.add_row(*new_row)
            elif row[0] in ["ok", "warning", "error", "failed"]:
                new_row = [
                    Text(cell_text, style=f"{self.row_color[row[0]]}")
                    for cell_text in row
                ]
                self.add_row(*new_row)
            elif row[0] == "info" and row[2] == "not set":
                new_row = [
                    Text(cell_text, style=self.row_color["warning"])
                    for cell_text in row
                ]
                self.add_row(*new_row)
            else:
                text_row = [Text(cell_text) for cell_text in row]
                self.add_row(*text_row)


class PwMgrInfo(Enum):
    age_command = PwMgrData(
        doctor_check="age-command",
        description="A simple, modern and secure file encryption tool.",
        link="https://github.com/FiloSottile/age",
        info=PwMgrStrings.fully_open_source,
    )
    bitwarden_command = PwMgrData(
        doctor_check="bitwarden-command",
        description="Bitwarden Password Manager",
        link="https://github.com/bitwarden",
        info=PwMgrStrings.source_available,
    )
    bitwarden_secrets_command = PwMgrData(
        doctor_check="bitwarden-secrets-command",
        description="Bitwarden Secrets Manager CLI for managing secrets securely.",
        link="https://github.com/bitwarden",
        info=PwMgrStrings.fully_open_source,
    )
    dashlane_command = PwMgrData(
        doctor_check="dashlane-command",
        description=(
            "Simple and secure access to all your online accounts. At work,"
            " home, and everywhere in between."
        ),
        link="https://github.com/dashlane",
        info=PwMgrStrings.not_open_source,
    )
    doppler_command = PwMgrData(
        doctor_check="doppler-command",
        description=(
            "Doppler is the multi-cloud SecretOps Platform developers and"
            " security teams trust to provide secrets management at enterprise scale."
        ),
        link="https://github.com/dopplerhq",
        info=PwMgrStrings.not_open_source,
    )
    gopass_command = PwMgrData(
        doctor_check="gopass-command",
        description=(
            "The slightly more awesome standard unix password manager for teams."
        ),
        link="https://github.com/gopasspw/gopass",
        info=PwMgrStrings.fully_open_source,
    )
    keeper_command = PwMgrData(
        doctor_check="keeper-command",
        description="An interface to Keeper Password Manager",
        link="https://github.com/Keeper-Security/Commander",
        info=PwMgrStrings.not_open_source,
    )
    keepassxc_command = PwMgrData(
        doctor_check="keepassxc-command",
        description=(
            "Cross-platform community-driven port of Keepass password manager."
        ),
        link="https://keepassxc.org/",
        info=PwMgrStrings.fully_open_source,
    )
    lastpass_command = PwMgrData(
        doctor_check="lastpass-command",
        description="Old LastPass CLI for accessing your LastPass vault.",
        link="https://https://github.com/lastpass",
        info=PwMgrStrings.not_open_source,
    )
    one_password_command = PwMgrData(
        doctor_check="one-password-command",
        description="Secure all sign-ins to every application from any device.",
        link="https://github.com/1Password/for-open-source",
        info=PwMgrStrings.not_open_source,
    )
    pass_command = PwMgrData(
        doctor_check="pass-command",
        description=(
            "Stores, retrieves, generates, and synchronizes passwords securely."
        ),
        link="https://www.passwordstore.org/",
        info=PwMgrStrings.confusing,
    )
    passhole_command = PwMgrData(
        doctor_check="passhole-command",
        description="A secure hole for your passwords (KeePass CLI).",
        link="https://github.com/Evidlo/passhole",
        info=PwMgrStrings.not_open_source,
    )
    pinentry_command = PwMgrData(
        doctor_check="pinentry-command",
        description=(
            "Collection of simple PIN or passphrase entry dialogs which utilize"
            " the Assuan protocol."
        ),
        link="https://gnupg.org/related_software/pinentry/",
        info=PwMgrStrings.fully_open_source,
    )
    rbw_command = PwMgrData(
        doctor_check="rbw-command",
        description="Unofficial Bitwarden.",
        link="https://git.tozt.net/rbw",
        info=PwMgrStrings.not_documented,
    )
    vault_command = PwMgrData(
        doctor_check="vault-command",
        description="A tool for managing secrets.",
        link="https://vaultproject.io/",
        info=PwMgrStrings.not_documented,
    )


class PwCollapsible(Collapsible):

    def __init__(self, pw_mgr_data: PwMgrData, dr_message: str) -> None:
        self.pw_mgr_data = pw_mgr_data
        self.dr_message = dr_message
        self.stripped_link = self.pw_mgr_data.link.replace("https://", "").replace(
            "www.", ""
        )

        super().__init__(
            VerticalGroup(
                Label(SectionLabel.project_link, classes=Tcss.sub_section_label),
                Link(self.stripped_link, url=self.pw_mgr_data.link),
                Label(SectionLabel.project_description, classes=Tcss.sub_section_label),
                Static(self.pw_mgr_data.description, markup=False),
                Label(
                    SectionLabel.pw_mgr_additional_info, classes=Tcss.sub_section_label
                ),
                Static(self.pw_mgr_data.info, markup=False),
                classes=Tcss.pw_mgr_group,
            ),
            title=(
                f"[${ColorVar.text_primary}]Doctor check: "
                f"{self.pw_mgr_data.doctor_check}[/] "
                f"[{ColorVar.dimmed}]({self.dr_message})[/]"
            ),
            collapsed_symbol=Chars.right_triangle,
            expanded_symbol=Chars.down_triangle,
            collapsed=True,
        )
