from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import Button, ContentSwitcher, Label, Pretty, Static

from chezmoi_mousse import IDS, AppType, CommandResult, FlatBtnLabel, SectionLabel, Tcss

from .common.actionables import FlatButtonsVertical
from .common.doctor_data import DoctorTable, PwMgrInfoView

__all__ = ["ConfigTab"]


class CatConfigView(Vertical, AppType):
    def __init__(self):
        super().__init__(id=IDS.config.view.cat_config)

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.cat_config_output, classes=Tcss.main_section_label)

    @work
    async def on_mount(self) -> None:
        if self.app.cmd_results.cat_config is not None:
            self.mount(Static(self.app.cmd_results.cat_config.std_out))


class ConfigTabSwitcher(ContentSwitcher, AppType):

    def __init__(self):
        super().__init__(initial=IDS.config.container.doctor)

    def compose(self) -> ComposeResult:
        yield DoctorTableView()
        yield PwMgrInfoView(ids=IDS.config)
        yield CatConfigView()
        yield IgnoredView()
        yield TemplateDataView()

    @work
    async def on_mount(self):
        if self.app.cmd_results.doctor is None:
            raise RuntimeError("cmd_results.doctor is None")
        doctor_view = self.query_one(IDS.config.container.doctor_q, DoctorTableView)
        doctor_view.populate_doctor_data(command_result=self.app.cmd_results.doctor)
        pw_mgr_info_view = self.query_one(IDS.config.view.pw_mgr_info_q, PwMgrInfoView)
        pw_mgr_info_view.populate_pw_mgr_info(self.app.cmd_results.doctor)
        ignored_view = self.query_one(IDS.config.view.ignored_q, IgnoredView)
        if self.app.cmd_results.ignored is None:
            raise RuntimeError("cmd_results.ignored is None")
        ignored_view.mount_ignored_output(self.app.cmd_results.ignored)


class IgnoredView(Vertical):
    def __init__(self):
        super().__init__(id=IDS.config.view.ignored)

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.ignored_output, classes=Tcss.main_section_label)

    def mount_ignored_output(self, command_result: CommandResult) -> None:
        self.mount(ScrollableContainer(Pretty(command_result.std_out.splitlines())))


class DoctorTableView(Vertical, AppType):

    def __init__(self) -> None:
        super().__init__(id=IDS.config.container.doctor)

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.doctor_output, classes=Tcss.main_section_label)

    def populate_doctor_data(self, command_result: CommandResult) -> None:
        self.mount(DoctorTable(ids=IDS.config, doctor_data=command_result))


class TemplateDataView(Vertical, AppType):
    def __init__(self):
        super().__init__(id=IDS.config.view.template_data)

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.template_data_output, classes=Tcss.main_section_label)

    @work
    async def on_mount(self) -> None:
        if self.app.parsed_template_data is not None:
            self.mount(Pretty(self.app.parsed_template_data))


class ConfigTab(Horizontal, AppType):

    def compose(self) -> ComposeResult:
        yield FlatButtonsVertical(
            ids=IDS.config,
            buttons=(
                FlatBtnLabel.doctor,
                FlatBtnLabel.pw_mgr_info,
                FlatBtnLabel.cat_config,
                FlatBtnLabel.ignored,
                FlatBtnLabel.template_data,
            ),
        )
        yield ConfigTabSwitcher()

    @on(Button.Pressed, Tcss.flat_button.dot_prefix)
    def switch_content(self, event: Button.Pressed) -> None:
        switcher = self.query_exactly_one(ConfigTabSwitcher)
        event.stop()
        if event.button.label == FlatBtnLabel.doctor:
            switcher.current = IDS.config.container.doctor
        if event.button.label == FlatBtnLabel.pw_mgr_info:
            switcher.current = IDS.config.view.pw_mgr_info
        elif event.button.label == FlatBtnLabel.cat_config:
            switcher.current = IDS.config.view.cat_config
        elif event.button.label == FlatBtnLabel.ignored:
            switcher.current = IDS.config.view.ignored
        elif event.button.label == FlatBtnLabel.template_data:
            switcher.current = IDS.config.view.template_data
