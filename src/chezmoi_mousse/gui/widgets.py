from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from rich.text import Text
from textual.reactive import reactive
from textual.widgets import DataTable, Link, ListItem, ListView, Static

from chezmoi_mousse import AppType, Id, ReadCmd, Tcss, ViewName

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["DoctorListView", "DoctorTable", "GitLogView"]


class GitLogView(DataTable[Text], AppType):

    path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, *, ids: "CanvasIds") -> None:
        self.ids = ids
        self.destDir: Path | None = None
        super().__init__(
            id=self.ids.view_id(view=ViewName.git_log_view),
            show_cursor=False,
            classes=Tcss.border_title_top.name,
        )

    def _add_row_with_style(self, columns: list[str], style: str) -> None:
        row: Iterable[Text] = [
            Text(cell_text, style=style) for cell_text in columns
        ]
        self.add_row(*row)

    def populate_data_table(self, cmd_output: str) -> None:
        self.clear(columns=True)
        self.add_columns("COMMIT", "MESSAGE")
        styles = {
            "ok": self.app.theme_variables["text-success"],
            "warning": self.app.theme_variables["text-warning"],
            "error": self.app.theme_variables["text-error"],
        }
        for line in cmd_output.splitlines():
            columns = line.split(";")
            if columns[1].split(maxsplit=1)[0] == "Add":
                self._add_row_with_style(columns, styles["ok"])
            elif columns[1].split(maxsplit=1)[0] == "Update":
                self._add_row_with_style(columns, styles["warning"])
            elif columns[1].split(maxsplit=1)[0] == "Remove":
                self._add_row_with_style(columns, styles["error"])
            else:
                self.add_row(*(Text(cell) for cell in columns))

    def watch_path(self) -> None:
        if self.path is None:
            return
        if self.path == self.destDir:
            cmd_output = self.app.chezmoi.read(ReadCmd.git_log)
        else:
            source_path = Path(
                self.app.chezmoi.read(ReadCmd.source_path, self.path)
            )
            cmd_output = self.app.chezmoi.read(ReadCmd.git_log, source_path)
        self.border_title = f" {self.path} "
        self.populate_data_table(cmd_output)


class DoctorTable(DataTable[Text], AppType):

    def __init__(self) -> None:
        self.pw_mgr_commands: list[str] = []
        super().__init__(
            id=Id.config_tab.datatable_id,
            show_cursor=False,
            classes=Tcss.doctor_table.name,
        )

    def populate_doctor_data(self, doctor_data: list[str]) -> list[str]:
        # TODO: create reactive var to run this so the app reacts on chezmoi config changes while running
        self.dr_style = {
            "ok": self.app.theme_variables["text-success"],
            "info": self.app.theme_variables["foreground-darken-1"],
            "warning": self.app.theme_variables["text-warning"],
            "failed": self.app.theme_variables["text-error"],
            "error": self.app.theme_variables["text-error"],
        }

        if not self.columns:
            self.add_columns(*doctor_data[0].split())

        for line in doctor_data[1:]:
            row = tuple(line.split(maxsplit=2))
            if row[0] == "info" and "not found in $PATH" in row[2]:
                self.pw_mgr_commands.append((row[1]))
                new_row = [
                    Text(cell_text, style=self.dr_style["info"])
                    for cell_text in row
                ]
                self.add_row(*new_row)
            elif row[0] in ["ok", "warning", "error", "failed"]:
                new_row = [
                    Text(cell_text, style=f"{self.dr_style[row[0]]}")
                    for cell_text in row
                ]
                self.add_row(*new_row)
            elif row[0] == "info" and row[2] == "not set":
                self.pw_mgr_commands.append((row[1]))
                new_row = [
                    Text(cell_text, style=self.dr_style["warning"])
                    for cell_text in row
                ]
                self.add_row(*new_row)
            else:
                row = [Text(cell_text) for cell_text in row]
                self.add_row(*row)
        return self.pw_mgr_commands


class DoctorListView(ListView):

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

    def __init__(self) -> None:
        super().__init__(
            id=Id.config_tab.listview_id, classes=Tcss.doctor_listview.name
        )

    def populate_listview(self, pw_mgr_commands: list[str]) -> None:
        for cmd in pw_mgr_commands:
            for pw_mgr in DoctorListView.PwMgrInfo:
                if pw_mgr.value.doctor_check == cmd:
                    self.append(
                        ListItem(
                            Link(cmd, url=pw_mgr.value.link),
                            Static(pw_mgr.value.description),
                        )
                    )
                    break
