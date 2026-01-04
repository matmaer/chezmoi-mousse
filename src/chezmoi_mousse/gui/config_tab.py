from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import Button, ContentSwitcher, Label, Pretty, Static

from chezmoi_mousse import (
    IDS,
    AppIds,
    AppType,
    CommandResult,
    FlatBtn,
    SectionLabels,
    SplashData,
    Tcss,
)

from .common.actionables import FlatButtonsVertical
from .common.doctor_table import DoctorTable
from .common.pretty_template_data import PrettyTemplateData
from .common.pw_mgr_info import PwMgrInfoView

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds


__all__ = [
    "ConfigTab",
    "ConfigTabSwitcher",
    "DoctorTableView",
    "TemplateDataView",
]


class CatConfigView(Vertical):
    def __init__(self, ids: "AppIds"):
        self.ids = ids
        super().__init__(id=self.ids.view.cat_config)

    def compose(self) -> ComposeResult:
        yield Label(
            SectionLabels.cat_config_output, classes=Tcss.main_section_label
        )

    def mount_cat_config_output(self, command_result: CommandResult) -> None:
        self.mount(ScrollableContainer(Static(command_result.std_out)))


class ConfigTabSwitcher(ContentSwitcher):

    splash_data: reactive["SplashData | None"] = reactive(None)

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

    def watch_splash_data(self):
        if self.splash_data is None:
            return

        doctor_view = self.query_one(
            IDS.config.container.doctor_q, DoctorTableView
        )
        doctor_view.populate_doctor_data(
            command_result=self.splash_data.doctor
        )
        pw_mgr_info_view = self.query_one(
            IDS.config.view.pw_mgr_info_q, PwMgrInfoView
        )
        pw_mgr_info_view.populate_pw_mgr_info(self.splash_data.doctor)

        cat_config_view = self.query_one(
            IDS.config.view.cat_config_q, CatConfigView
        )
        cat_config_view.mount_cat_config_output(self.splash_data.cat_config)

        ignored_view = self.query_one(IDS.config.view.ignored_q, IgnoredView)
        ignored_view.mount_ignored_output(self.splash_data.ignored)

        template_data_view = self.query_one(
            IDS.config.view.template_data_q, TemplateDataView
        )
        template_data_view.mount_template_data_output(
            self.splash_data.template_data
        )


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


class TemplateDataView(Vertical):
    def __init__(self, ids: "AppIds"):
        self.ids = ids
        super().__init__(id=self.ids.view.template_data)

    def compose(self) -> ComposeResult:
        yield Label(
            SectionLabels.template_data_output, classes=Tcss.main_section_label
        )

    def mount_template_data_output(
        self, command_result: CommandResult
    ) -> None:
        self.mount(PrettyTemplateData(template_data=command_result))


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
