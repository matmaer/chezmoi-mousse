from typing import TYPE_CHECKING

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import Button, ContentSwitcher, Label, Pretty, Static

from chezmoi_mousse import (
    IDS,
    AppIds,
    AppType,
    CommandResult,
    FlatBtn,
    SectionLabels,
    Tcss,
)

from .common.actionables import FlatButtonsVertical
from .common.doctor_data import DoctorTable, PwMgrInfoView

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds


__all__ = ["ConfigTab"]


class CatConfigView(Vertical, AppType):
    def __init__(self, ids: "AppIds"):
        self.ids = ids
        super().__init__(id=self.ids.view.cat_config)

    def compose(self) -> ComposeResult:
        yield Label(
            SectionLabels.cat_config_output, classes=Tcss.main_section_label
        )

    @work
    async def on_mount(self) -> None:
        if self.app.cmd_results.cat_config is not None:
            self.mount(Static(self.app.cmd_results.cat_config.std_out))


class ConfigTabSwitcher(ContentSwitcher, AppType):

    def __init__(self):
        super().__init__(
            id=IDS.config.switcher.config_tab,
            initial=IDS.config.container.doctor,
        )

    def compose(self) -> ComposeResult:
        yield DoctorTableView(ids=IDS.config)
        yield PwMgrInfoView(ids=IDS.config)
        yield CatConfigView(ids=IDS.config)
        yield IgnoredView(ids=IDS.config)
        yield TemplateDataView(ids=IDS.config)

    @work
    async def on_mount(self):
        if self.app.cmd_results.doctor is None:
            raise RuntimeError("cmd_results.doctor is None")
        doctor_view = self.query_one(
            IDS.config.container.doctor_q, DoctorTableView
        )
        doctor_view.populate_doctor_data(
            command_result=self.app.cmd_results.doctor
        )
        pw_mgr_info_view = self.query_one(
            IDS.config.view.pw_mgr_info_q, PwMgrInfoView
        )
        pw_mgr_info_view.populate_pw_mgr_info(self.app.cmd_results.doctor)
        ignored_view = self.query_one(IDS.config.view.ignored_q, IgnoredView)
        if self.app.cmd_results.ignored is None:
            raise RuntimeError("cmd_results.ignored is None")
        ignored_view.mount_ignored_output(self.app.cmd_results.ignored)


class IgnoredView(Vertical):
    def __init__(self, ids: "AppIds"):
        self.ids = ids
        super().__init__(id=self.ids.view.ignored)

    def compose(self) -> ComposeResult:
        yield Label(
            SectionLabels.ignored_output, classes=Tcss.main_section_label
        )

    def mount_ignored_output(self, command_result: CommandResult) -> None:
        self.mount(
            ScrollableContainer(Pretty(command_result.std_out.splitlines()))
        )


class DoctorTableView(Vertical, AppType):

    def __init__(self, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.container.doctor)

    def compose(self) -> ComposeResult:
        yield Label(
            SectionLabels.doctor_output, classes=Tcss.main_section_label
        )

    def populate_doctor_data(self, command_result: CommandResult) -> None:
        self.mount(DoctorTable(ids=self.ids, doctor_data=command_result))


class TemplateDataView(Vertical, AppType):
    def __init__(self, ids: "AppIds"):
        self.ids = ids
        super().__init__(id=self.ids.view.template_data)

    def compose(self) -> ComposeResult:
        yield Label(
            SectionLabels.template_data_output, classes=Tcss.main_section_label
        )

    @work
    async def on_mount(self) -> None:
        if self.app.parsed_template_data is not None:
            self.mount(Pretty(self.app.parsed_template_data))


class ConfigTab(Horizontal, AppType):

    def compose(self) -> ComposeResult:
        yield FlatButtonsVertical(
            ids=IDS.config,
            buttons=(
                FlatBtn.doctor,
                FlatBtn.pw_mgr_info,
                FlatBtn.cat_config,
                FlatBtn.ignored,
                FlatBtn.template_data,
            ),
        )
        yield ConfigTabSwitcher()

    @on(Button.Pressed, Tcss.flat_button.dot_prefix)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_one(
            IDS.config.switcher.config_tab_q, ConfigTabSwitcher
        )
        if event.button.id == IDS.config.flat_btn.doctor:
            switcher.current = IDS.config.container.doctor
        if event.button.id == IDS.config.flat_btn.pw_mgr_info:
            switcher.current = IDS.config.view.pw_mgr_info
        elif event.button.id == IDS.config.flat_btn.cat_config:
            switcher.current = IDS.config.view.cat_config
        elif event.button.id == IDS.config.flat_btn.ignored:
            switcher.current = IDS.config.view.ignored
        elif event.button.id == IDS.config.flat_btn.template_data:
            switcher.current = IDS.config.view.template_data
