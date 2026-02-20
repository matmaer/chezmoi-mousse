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
    cat_config_stdout: reactive[str | None] = reactive(None)

    def __init__(self):
        super().__init__(id=IDS.config.view.cat_config)

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.cat_config_output, classes=Tcss.main_section_label)

    def watch_cat_config_stdout(self) -> None:
        if self.cat_config_stdout is not None:
            self.mount(Static(self.cat_config_stdout))


class IgnoredView(Vertical):

    ignored_stdout: reactive[str | None] = reactive(None)

    def __init__(self):
        super().__init__(id=IDS.config.view.ignored)

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.ignored_output, classes=Tcss.main_section_label)
        yield ScrollableContainer(Pretty(()))

    def watch_ignored_stdout(self) -> None:
        if self.ignored_stdout is not None:
            pretty = self.query_exactly_one(Pretty)
            pretty.update(self.ignored_stdout.splitlines())


class DoctorTableView(Vertical, AppType):

    doctor_stdout: reactive[str | None] = reactive(None)

    def __init__(self) -> None:
        super().__init__(id=IDS.config.container.doctor)

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.doctor_output, classes=Tcss.main_section_label)
        yield DoctorTable()

    def watch_doctor_stdout(self) -> None:
        if self.doctor_stdout is not None:
            doctor_table = self.query_exactly_one(DoctorTable)
            doctor_table.doctor_std_out = self.doctor_stdout


class TemplateDataView(Vertical, AppType):

    template_data_stdout: reactive[str | None] = reactive(None)

    def __init__(self):
        super().__init__(id=IDS.config.view.template_data)

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.template_data_output, classes=Tcss.main_section_label)
        yield Pretty("No template data output yet.")

    def watch_template_data_stdout(self) -> None:
        if self.template_data_stdout is not None:
            parsed = json.loads(self.template_data_stdout)
            pretty = self.query_exactly_one(Pretty)
            pretty.update(parsed)


class ConfigTab(Horizontal, AppType):

    command_results: reactive["CommandResults | None"] = reactive(None)

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

    def watch_command_results(self) -> None:
        if self.command_results is None:
            return
        new = self.command_results
        if (
            new.cat_config is None
            or new.doctor is None
            or new.ignored is None
            or new.template_data is None
        ):
            return
        switcher = self.query_exactly_one(ContentSwitcher)
        switcher.query_one(
            IDS.config.view.template_data_q, TemplateDataView
        ).template_data_stdout = new.template_data.completed_process.stdout
        switcher.query_one(IDS.config.view.ignored_q, IgnoredView).ignored_stdout = (
            new.ignored.completed_process.stdout
        )
        switcher.query_one(
            IDS.config.view.cat_config_q, CatConfigView
        ).cat_config_stdout = new.cat_config.completed_process.stdout
        switcher.query_one(
            IDS.config.container.doctor_q, DoctorTableView
        ).doctor_stdout = new.doctor.completed_process.stdout
        switcher.query_one(
            IDS.config.view.pw_mgr_info_q, PwMgrInfoView
        ).populate_pw_mgr_info(new.doctor.completed_process.stdout)
