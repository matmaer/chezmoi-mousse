import json
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import Button, ContentSwitcher, Label, Pretty, Static

from chezmoi_mousse import IDS, AppType, FlatBtnLabel, SectionLabel, Tcss

from .common.actionables import FlatButtonsVertical
from .common.doctor_data import DoctorTable, PwMgrInfoView

if TYPE_CHECKING:
    from chezmoi_mousse import CommandResults

__all__ = ["ConfigTab"]


class CatConfigView(Vertical, AppType):

    cat_config_stdout: reactive[str | None] = reactive(None, init=False)

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.cat_config_output, classes=Tcss.main_section_label)

    def watch_cat_config_stdout(self, cat_config_stdout: str) -> None:
        self.mount(Static(cat_config_stdout))


class IgnoredView(Vertical):

    ignored_stdout: reactive[str | None] = reactive(None, init=False)

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.ignored_output, classes=Tcss.main_section_label)
        yield ScrollableContainer(Pretty(()))

    def watch_ignored_stdout(self, ignored_stdout: str) -> None:
        pretty = self.query_exactly_one(Pretty)
        pretty.update(ignored_stdout.splitlines())


class DoctorTableView(Vertical, AppType):

    doctor_stdout: reactive[str | None] = reactive(None, init=False)

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.doctor_output, classes=Tcss.main_section_label)
        yield DoctorTable()

    def watch_doctor_stdout(self, doctor_stdout: str) -> None:
        doctor_table = self.query_exactly_one(DoctorTable)
        doctor_table.doctor_std_out = doctor_stdout


class TemplateDataView(Vertical, AppType):

    template_data_stdout: reactive[str | None] = reactive(None, init=False)

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.template_data_output, classes=Tcss.main_section_label)
        yield Pretty("No template data output yet.")

    def watch_template_data_stdout(self, template_data_stdout: str) -> None:
        pretty = self.query_exactly_one(Pretty)
        pretty.update(json.loads(template_data_stdout))


class ConfigTab(Horizontal, AppType):

    command_results: reactive["CommandResults | None"] = reactive(None, init=False)

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
            yield DoctorTableView(id=IDS.config.container.doctor)
            yield PwMgrInfoView(id=IDS.config.view.pw_mgr_info)
            yield CatConfigView(id=IDS.config.view.cat_config)
            yield IgnoredView(id=IDS.config.view.ignored)
            yield TemplateDataView(id=IDS.config.view.template_data)

    def on_mount(self) -> None:
        self.switcher = self.query_exactly_one(ContentSwitcher)

    @on(Button.Pressed, Tcss.flat_button.dot_prefix)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == FlatBtnLabel.doctor:
            self.switcher.current = IDS.config.container.doctor
        if event.button.label == FlatBtnLabel.pw_mgr_info:
            self.switcher.current = IDS.config.view.pw_mgr_info
        elif event.button.label == FlatBtnLabel.cat_config:
            self.switcher.current = IDS.config.view.cat_config
        elif event.button.label == FlatBtnLabel.ignored:
            self.switcher.current = IDS.config.view.ignored
        elif event.button.label == FlatBtnLabel.template_data:
            self.switcher.current = IDS.config.view.template_data

    def watch_command_results(self, command_results: "CommandResults") -> None:
        if (
            command_results.cat_config is None
            or command_results.doctor is None
            or command_results.ignored is None
            or command_results.template_data is None
        ):
            return
        self.switcher.query_one(
            IDS.config.view.template_data_q, TemplateDataView
        ).template_data_stdout = command_results.template_data.completed_process.stdout
        self.switcher.query_one(
            IDS.config.view.ignored_q, IgnoredView
        ).ignored_stdout = command_results.ignored.completed_process.stdout
        self.switcher.query_one(
            IDS.config.view.cat_config_q, CatConfigView
        ).cat_config_stdout = command_results.cat_config.completed_process.stdout
        self.switcher.query_one(
            IDS.config.container.doctor_q, DoctorTableView
        ).doctor_stdout = command_results.doctor.completed_process.stdout
        self.switcher.query_one(
            IDS.config.view.pw_mgr_info_q, PwMgrInfoView
        ).populate_pw_mgr_info(command_results.doctor.completed_process.stdout)
