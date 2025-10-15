"""Contains classes which inherit from textual widgets."""

# RULES: These classes
# - inherit directly from built in textual widgets
# - are not containers, but can be focussable or not
# - don't override the parents' compose method
# - don't call any query methods
# - don't import from main_tabs.py, gui.py or containers.py modules
# - don't have key bindings
# - don't access any self.app in their __init__ method
# - don't access self.app attributes in their on_mount method which are updated after the loading screen completes in the App class on_mount method
# don't init any textual classes in the __init__  or on_mount method

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum, StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from rich.text import Text
from textual.reactive import reactive
from textual.widgets import DataTable, Link, ListItem, ListView, Static

from chezmoi_mousse import (
    AppType,
    Chars,
    Id,
    OperateBtn,
    ReadCmd,
    Tcss,
    ViewName,
)

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["DoctorListView", "DoctorTable", "GitLogView", "OperateInfo"]


class OperateInfo(Static, AppType):

    git_autocommit: bool | None = None
    git_autopush: bool | None = None

    class Strings(StrEnum):
        container_id = "operate_help"
        add_file = "[$text-primary]Path will be added to your chezmoi dotfile manager source state.[/]"
        apply_file = "[$text-primary]The file in the destination directory will be modified.[/]"
        # apply_dir = "[$text-primary]The directory in the destination directory will be modified.[/]"
        auto_commit = f"[$text-warning]{Chars.warning_sign} Auto commit is enabled: files will also be committed.{Chars.warning_sign}[/]"
        autopush = f"[$text-warning]{Chars.warning_sign} Auto push is enabled: files will be pushed to the remote.{Chars.warning_sign}[/]"
        destroy_file = "[$text-error]Permanently remove the file both from your home directory and chezmoi's source directory, make sure you have a backup![/]"
        # destroy_dir = "[$text-error]Permanently remove the directory both from your home directory and chezmoi's source directory, make sure you have a backup![/]"
        diff_color = "[$text-success]+ green lines will be added[/]\n[$text-error]- red lines will be removed[/]\n[dim]{Chars.bullet} dimmed lines for context[/]"
        forget_file = "[$text-primary]Remove the file from the source state, i.e. stop managing them.[/]"
        # forget_dir = "[$text-primary]Remove the directory from the source state, i.e. stop managing them.[/]"
        re_add_file = "[$text-primary]Overwrite the source state with current local file[/]"
        # re_add_dir = "[$text-primary]Overwrite the source state with thecurrent local directory[/]"

    def __init__(self, *, operate_btn: OperateBtn) -> None:
        self.operate_btn = operate_btn
        super().__init__(
            id=OperateInfo.Strings.container_id, classes=Tcss.operate_info.name
        )

    def on_mount(self) -> None:
        lines_to_write: list[str] = []

        # show command help and set the subtitle
        if OperateBtn.apply_file == self.operate_btn:
            lines_to_write.append(OperateInfo.Strings.apply_file.value)
            self.border_subtitle = Chars.apply_file_info_border
        elif OperateBtn.re_add_file == self.operate_btn:
            lines_to_write.append(OperateInfo.Strings.re_add_file.value)
            self.border_subtitle = Chars.re_add_file_info_border
        elif OperateBtn.add_file == self.operate_btn:
            lines_to_write.append(OperateInfo.Strings.add_file.value)
            self.border_subtitle = Chars.add_file_info_border
        elif OperateBtn.forget_file == self.operate_btn:
            lines_to_write.append(OperateInfo.Strings.forget_file.value)
            self.border_subtitle = Chars.forget_file_info_border
        elif OperateBtn.destroy_file == self.operate_btn:
            lines_to_write.extend(OperateInfo.Strings.destroy_file.value)
            self.border_subtitle = Chars.destroy_file_info_border
        # show git auto warnings
        if not OperateBtn.apply_file == self.operate_btn:
            assert (
                self.git_autocommit is not None
                and self.git_autopush is not None
            )
            if self.git_autocommit is True:
                lines_to_write.append(OperateInfo.Strings.auto_commit.value)
            if self.git_autopush is True:
                lines_to_write.append(OperateInfo.Strings.autopush.value)
        # show git diff color info
        if (
            OperateBtn.apply_file == self.operate_btn
            or OperateBtn.re_add_file == self.operate_btn
        ):
            lines_to_write.extend(OperateInfo.Strings.diff_color.value)
        self.update("\n".join(lines_to_write))


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
