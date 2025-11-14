import json
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import (
    Horizontal,
    ScrollableContainer,
    Vertical,
    VerticalScroll,
)
from textual.reactive import reactive
from textual.widgets import (
    Button,
    ContentSwitcher,
    Link,
    ListItem,
    ListView,
    Pretty,
    Static,
)

from chezmoi_mousse import AppType, ContainerName, FlatBtn, Tcss, ViewName
from chezmoi_mousse.shared import (
    CatConfigOutput,
    DoctorTable,
    FlatButtonsVertical,
    MainSectionLabelText,
    SectionLabel,
)

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds, CommandResult

__all__ = ["ConfigTab", "ConfigTabSwitcher"]


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
        )
        self.doctor_table_qid = ids.datatable_id(
            "#", view_name=ViewName.doctor_view
        )

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            SectionLabel(MainSectionLabelText.doctor_output),
            DoctorTable(ids=self.ids),
            SectionLabel(MainSectionLabelText.password_managers),
            DoctorListView(ids=self.ids),
            id=self.doctor_list_view_id,
            classes=Tcss.doctor_vertical_scroll.name,
        )
        yield CatConfigOutput(ids=self.ids)
        yield ScrollableContainer(
            SectionLabel(MainSectionLabelText.ignored_output),
            Pretty("<ignored>", id=ViewName.pretty_ignored_view),
            id=self.ids.view_id(view=ViewName.git_ignored_view),
        )
        yield ScrollableContainer(
            SectionLabel(MainSectionLabelText.template_data_output),
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


class ConfigTab(Horizontal, AppType):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.tab_container_id)

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
