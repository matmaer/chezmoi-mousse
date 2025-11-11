import json
from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import TYPE_CHECKING

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import (
    Button,
    ContentSwitcher,
    DataTable,
    Link,
    ListItem,
    ListView,
    Pretty,
    Static,
)

from chezmoi_mousse import AppType, ContainerName, FlatBtn, Tcss, ViewName

from .shared.buttons import FlatButtonsVertical
from .shared.section_headers import SectionLabel
from .shared.tabs_base import TabsBase

if TYPE_CHECKING:
    from chezmoi_mousse import CommandResult

    from .shared.canvas_ids import CanvasIds

__all__ = ["ConfigTab", "ConfigTabSwitcher"]


class Strings(StrEnum):
    cat_config_output = '"chezmoi cat-config" output'
    doctor_output = '"chezmoi doctor" output'
    ignored_output = '"chezmoi ignored" output'
    password_managers = "Password managers not found in $PATH"
    template_data_output = '"chezmoi data" output'


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


class DoctorTable(DataTable[Text], AppType):

    def __init__(self, ids: "CanvasIds") -> None:

        super().__init__(
            id=ids.datatable_id(view_name=ViewName.doctor_view),
            show_cursor=False,
            classes=Tcss.doctor_table.name,
        )

        self.pw_mgr_commands: list[str] = []

    def on_mount(self) -> None:
        self.dr_style = {
            "ok": self.app.theme_variables["text-success"],
            "info": self.app.theme_variables["foreground-darken-1"],
            "warning": self.app.theme_variables["text-warning"],
            "failed": self.app.theme_variables["text-error"],
            "error": self.app.theme_variables["text-error"],
        }

    def populate_doctor_data(self, doctor_data: list[str]) -> list[str]:

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

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.listview_id, classes=Tcss.doctor_listview.name
        )

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


class ConfigTabSwitcher(ContentSwitcher):

    doctor_results: reactive["CommandResult | None"] = reactive(None)
    cat_config_results: reactive["CommandResult | None"] = reactive(None)
    ignored_results: reactive["CommandResult | None"] = reactive(None)
    template_data_results: reactive["CommandResult | None"] = reactive(None)

    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        self.doctor_list_view_id = self.ids.view_id(view=ViewName.doctor_view)
        super().__init__(
            id=self.ids.content_switcher_id(
                name=ContainerName.config_switcher
            ),
            initial=self.doctor_list_view_id,
            classes=Tcss.nav_content_switcher.name,
        )
        self.doctor_table_qid = ids.datatable_id(
            "#", view_name=ViewName.doctor_view
        )

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            SectionLabel(Strings.doctor_output),
            DoctorTable(ids=self.ids),
            SectionLabel(Strings.password_managers),
            DoctorListView(ids=self.ids),
            id=self.doctor_list_view_id,
            classes=Tcss.doctor_vertical_scroll.name,
        )
        yield Vertical(
            SectionLabel(Strings.cat_config_output),
            Pretty("<cat-config>", id=ViewName.pretty_cat_config_view),
            id=self.ids.view_id(view=ViewName.cat_config_view),
        )
        yield Vertical(
            SectionLabel(Strings.ignored_output),
            Pretty("<ignored>", id=ViewName.pretty_ignored_view),
            id=self.ids.view_id(view=ViewName.git_ignored_view),
        )
        yield Vertical(
            SectionLabel(Strings.template_data_output),
            Pretty("<template_data>", id=ViewName.pretty_template_data_view),
            id=self.ids.view_id(view=ViewName.template_data_view),
        )

    def watch_doctor_results(self):
        doctor_table = self.query_one(self.doctor_table_qid, DoctorTable)
        if self.doctor_results is None:
            return
        pw_mgr_cmds: list[str] = doctor_table.populate_doctor_data(
            doctor_data=self.doctor_results.std_out.splitlines()
        )
        doctor_list_view = self.query_one(
            self.ids.listview_qid, DoctorListView
        )
        doctor_list_view.populate_listview(pw_mgr_cmds)

    def watch_cat_config_results(self):
        if self.cat_config_results is None:
            return
        pretty_cat_config = self.query_one(
            f"#{ViewName.pretty_cat_config_view}", Pretty
        )
        pretty_cat_config.update(self.cat_config_results.std_out.splitlines())

    def watch_ignored_results(self):
        if self.ignored_results is None:
            return
        pretty_ignored = self.query_one(
            f"#{ViewName.pretty_ignored_view}", Pretty
        )
        pretty_ignored.update(self.ignored_results.std_out.splitlines())

    def watch_template_data_results(self):
        if self.template_data_results is None:
            return
        pretty_template_data = self.query_one(
            f"#{ViewName.pretty_template_data_view}", Pretty
        )
        template_data_json = json.loads(self.template_data_results.std_out)
        pretty_template_data.update(template_data_json)


class ConfigTab(TabsBase, AppType):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(ids=self.ids)

        self.tab_vertical_id = ids.tab_vertical_id(
            name=ContainerName.left_side
        )
        self.content_switcher_id = self.ids.content_switcher_id(
            name=ContainerName.config_switcher
        )
        self.content_switcher_qid = self.ids.content_switcher_id(
            "#", name=ContainerName.config_switcher
        )

        # Button IDs
        self.cat_config_btn_id = self.ids.button_id(btn=(FlatBtn.cat_config))
        self.doctor_btn_id = self.ids.button_id(btn=(FlatBtn.doctor))
        self.ignored_btn_id = self.ids.button_id(btn=FlatBtn.ignored)
        self.template_data_btn_id = self.ids.button_id(
            btn=FlatBtn.template_data
        )
        # View IDs
        self.cat_config_view_id = self.ids.view_id(
            view=ViewName.cat_config_view
        )
        self.doctor_view_id = self.ids.view_id(view=ViewName.doctor_view)
        self.ignored_view_id = self.ids.view_id(view=ViewName.git_ignored_view)
        self.template_data_view_id = self.ids.view_id(
            view=ViewName.template_data_view
        )

    def compose(self) -> ComposeResult:
        with Vertical(
            id=self.tab_vertical_id, classes=Tcss.tab_left_vertical.name
        ):
            yield FlatButtonsVertical(
                ids=self.ids,
                buttons=(
                    FlatBtn.doctor,
                    FlatBtn.cat_config,
                    FlatBtn.ignored,
                    FlatBtn.template_data,
                ),
            )
        yield ConfigTabSwitcher(self.ids)

    @on(Button.Pressed, Tcss.flat_button.value)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_one(self.content_switcher_qid, ContentSwitcher)
        if event.button.id == self.doctor_btn_id:
            switcher.current = self.doctor_view_id
        elif event.button.id == self.cat_config_btn_id:
            switcher.current = self.cat_config_view_id
        elif event.button.id == self.ignored_btn_id:
            switcher.current = self.ignored_view_id
        elif event.button.id == self.template_data_btn_id:
            switcher.current = self.template_data_view_id
