import json
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import Button, ContentSwitcher, Label, Pretty, Static, TabPane

from chezmoi_mousse import AppIds, FlatBtnLabel, SectionLabel, TabLabel, Tcss

from .common.actionables import FlatButtonsVertical
from .common.doctor_data import DoctorTable, PwMgrInfoView

if TYPE_CHECKING:
    from chezmoi_mousse import CachedData

__all__ = ["ConfigTab"]


class CatConfigView(Vertical):

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


class DiagramView(Vertical):

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.diagram, classes=Tcss.main_section_label)
        yield Static(FLOW_DIAGRAM, classes=Tcss.flow_diagram)


class DoctorTableView(Vertical):

    doctor_stdout: reactive[str | None] = reactive(None, init=False)

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.doctor_output, classes=Tcss.main_section_label)
        yield DoctorTable()

    def watch_doctor_stdout(self, doctor_stdout: str) -> None:
        doctor_table = self.query_exactly_one(DoctorTable)
        doctor_table.doctor_std_out = doctor_stdout


class TemplateDataView(Vertical):

    template_data_stdout: reactive[str | None] = reactive(None, init=False)

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.template_data_output, classes=Tcss.main_section_label)
        yield Pretty("No template data output yet.")

    def watch_template_data_stdout(self, template_data_stdout: str) -> None:
        pretty = self.query_exactly_one(Pretty)
        pretty.update(json.loads(template_data_stdout))


class ConfigTab(TabPane):

    command_results: reactive["CachedData | None"] = reactive(None, init=False)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=TabLabel.config, title=TabLabel.config)
        self.ids = ids

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield FlatButtonsVertical(
                self.ids,
                buttons=(
                    FlatBtnLabel.doctor,
                    FlatBtnLabel.pw_mgr_info,
                    FlatBtnLabel.cat_config,
                    FlatBtnLabel.ignored,
                    FlatBtnLabel.template_data,
                    FlatBtnLabel.diagram,
                ),
            )
            with ContentSwitcher(initial=self.ids.container.doctor):
                yield DoctorTableView(id=self.ids.container.doctor)
                yield PwMgrInfoView(id=self.ids.view.pw_mgr_info)
                yield CatConfigView(id=self.ids.view.cat_config)
                yield IgnoredView(id=self.ids.view.ignored)
                yield TemplateDataView(id=self.ids.view.template_data)
                yield DiagramView(id=self.ids.view.diagram)

    def on_mount(self) -> None:
        self.switcher = self.query_exactly_one(ContentSwitcher)

    @on(Button.Pressed, Tcss.flat_button.dot_prefix)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == FlatBtnLabel.doctor:
            self.switcher.current = self.ids.container.doctor
        if event.button.label == FlatBtnLabel.pw_mgr_info:
            self.switcher.current = self.ids.view.pw_mgr_info
        elif event.button.label == FlatBtnLabel.cat_config:
            self.switcher.current = self.ids.view.cat_config
        elif event.button.label == FlatBtnLabel.ignored:
            self.switcher.current = self.ids.view.ignored
        elif event.button.label == FlatBtnLabel.template_data:
            self.switcher.current = self.ids.view.template_data
        elif event.button.label == FlatBtnLabel.diagram:
            self.switcher.current = self.ids.view.diagram

    def watch_command_results(self, cached: "CachedData") -> None:
        if (
            cached.cmd_results.cat_config is None
            or cached.cmd_results.doctor is None
            or cached.cmd_results.ignored is None
            or cached.cmd_results.template_data is None
        ):
            return
        self.switcher.query_one(
            self.ids.view.template_data_q, TemplateDataView
        ).template_data_stdout = (
            cached.cmd_results.template_data.completed_process.stdout
        )
        self.switcher.query_one(self.ids.view.ignored_q, IgnoredView).ignored_stdout = (
            cached.cmd_results.ignored.completed_process.stdout
        )
        self.switcher.query_one(
            self.ids.view.cat_config_q, CatConfigView
        ).cat_config_stdout = cached.cmd_results.cat_config.completed_process.stdout
        self.switcher.query_one(
            self.ids.container.doctor_q, DoctorTableView
        ).doctor_stdout = cached.cmd_results.doctor.completed_process.stdout
        self.switcher.query_one(
            self.ids.view.pw_mgr_info_q, PwMgrInfoView
        ).populate_pw_mgr_info(cached.cmd_results.doctor.completed_process.stdout)


FLOW_DIAGRAM = """\
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│home directory│    │ working copy │    │  local repo  │    │ remote repo  │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │                   │
       │                   │                   │                   │
       │     Add Tab       │    autoCommit     │     git push      │
       │   Re-Add Tab      │──────────────────>│──────────────────>│
       │──────────────────>│                   │                   │
       │                   │                autopush               │
       │                   │──────────────────────────────────────>│
       │                   │                   │                   │
       │                   │                   │                   │
       │     Apply Tab     │     chezmoi init & chezmoi git pull   │
       │<──────────────────│<──────────────────────────────────────│
       │                   │                   │                   │
       │     Diff View     │                   │                   │
       │<─ ─ ─ ─ ─ ─ ─ ─ ─>│                   │                   │
       │                   │                   │                   │
       │                   │    chezmoi init & chezmoi git pull    │
       │                   │<──────────────────────────────────────│
       │                   │                   │                   │
       │        chezmoi init --one-shot & chezmoi init --apply     │
       │<──────────────────────────────────────────────────────────│
       │                   │                   │                   │
┌──────┴───────┐    ┌──────┴───────────────────┴───────┐    ┌──────┴───────┐
│ destination  │    │    target state / source state   │    │  git remote  │
└──────────────┘    └──────────────────────────────────┘    └──────────────┘
"""
