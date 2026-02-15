import json

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import Button, ContentSwitcher, Label, Pretty, Static

from chezmoi_mousse import IDS, AppType, CmdResults, FlatBtnLabel, SectionLabel, Tcss

from .common.actionables import FlatButtonsVertical
from .common.doctor_data import DoctorTable, PwMgrInfoView

__all__ = ["ConfigTab"]


class CatConfigView(Vertical, AppType):
    cat_config_stdout: reactive[str | None] = reactive(None)

    def __init__(self):
        super().__init__(id=IDS.config.view.cat_config)

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.cat_config_output, classes=Tcss.main_section_label)

    def watch_cat_config_stdout(self) -> None:
        if self.cat_config_stdout is not None:
            # self.remove_children(Static)
            self.mount(Static(self.cat_config_stdout))


class IgnoredView(Vertical):

    ignored_stdout: reactive[str | None] = reactive(None)

    def __init__(self):
        super().__init__(id=IDS.config.view.ignored)

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.ignored_output, classes=Tcss.main_section_label)

    def watch_ignored_stdout(self) -> None:
        if self.ignored_stdout is not None:
            self.remove_children(ScrollableContainer)
            self.mount(ScrollableContainer(Pretty(self.ignored_stdout.splitlines())))


class DoctorTableView(Vertical, AppType):

    doctor_stdout: reactive[str | None] = reactive(None)

    def __init__(self) -> None:
        super().__init__(id=IDS.config.container.doctor)

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.doctor_output, classes=Tcss.main_section_label)

    def watch_doctor_stdout(self) -> None:
        if self.doctor_stdout is not None:
            self.remove_children(DoctorTable)
            self.mount(DoctorTable(doctor_stdout=self.doctor_stdout))


class TemplateDataView(Vertical, AppType):

    template_data_stdout: reactive[str | None] = reactive(None)

    def __init__(self):
        super().__init__(id=IDS.config.view.template_data)

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.template_data_output, classes=Tcss.main_section_label)

    def watch_template_data_stdout(self) -> None:
        if self.template_data_stdout is not None:
            self.remove_children(Pretty)
            self.mount(Pretty(json.loads(self.template_data_stdout)))


class ConfigTab(Horizontal, AppType):

    new_command_results: reactive[CmdResults | None] = reactive(None)

    def compose(self) -> ComposeResult:
        yield FlatButtonsVertical(
            IDS.config,
            buttons=(
                FlatBtnLabel.doctor,
                FlatBtnLabel.pw_mgr_info,
                FlatBtnLabel.cat_config,
                FlatBtnLabel.ignored,
                FlatBtnLabel.template_data,
            ),
        )
        with ContentSwitcher(initial=IDS.config.container.doctor):
            yield DoctorTableView()
            yield PwMgrInfoView()
            yield CatConfigView()
            yield IgnoredView()
            yield TemplateDataView()

    @on(Button.Pressed, Tcss.flat_button.dot_prefix)
    def switch_content(self, event: Button.Pressed) -> None:
        switcher = self.query_exactly_one(ContentSwitcher)
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

    def watch_new_command_results(self) -> None:
        if self.new_command_results is None:
            return
        new = self.new_command_results
        if (
            new.cat_config_results is None
            or new.doctor_results is None
            or new.ignored_results is None
            or new.template_data_results is None
        ):
            return
        switcher = self.query_exactly_one(ContentSwitcher)
        switcher.query_one(
            IDS.config.view.template_data_q, TemplateDataView
        ).template_data_stdout = new.template_data_results.completed_process.stdout
        switcher.query_one(IDS.config.view.ignored_q, IgnoredView).ignored_stdout = (
            new.ignored_results.completed_process.stdout
        )
        switcher.query_one(
            IDS.config.view.cat_config_q, CatConfigView
        ).cat_config_stdout = new.cat_config_results.completed_process.stdout
        switcher.query_one(
            IDS.config.container.doctor_q, DoctorTableView
        ).doctor_stdout = new.doctor_results.completed_process.stdout
        switcher.query_one(
            IDS.config.view.pw_mgr_info_q, PwMgrInfoView
        ).populate_pw_mgr_info(new.doctor_results.completed_process.stdout)
