from enum import StrEnum

from textual import on
from textual.app import ComposeResult
from textual.containers import (
    Horizontal,
    HorizontalGroup,
    Vertical,
    VerticalGroup,
)
from textual.screen import Screen
from textual.validation import URL
from textual.widgets import (
    Button,
    ContentSwitcher,
    Footer,
    Input,
    Select,
    Static,
)

from chezmoi_mousse import (
    IDS,
    AppType,
    BindingAction,
    BindingDescription,
    FlatBtn,
    OperateBtn,
    OperateData,
    SectionLabels,
    Tcss,
)
from chezmoi_mousse.shared import (
    CustomHeader,
    DebugLog,
    DoctorTableView,
    FlatButtonsVertical,
    MainSectionLabel,
    OperateButtonMsg,
    OperateButtons,
    SubSectionLabel,
    TemplateDataView,
)

from .operate import OperateScreen

__all__ = ["InitScreen"]


class StaticText(StrEnum):
    init_new = f"Initialize a new chezmoi repository in your home directory.\nClick the [$text-primary]{OperateBtn.init_new_repo.initial_label}[/] button below to run [$text-success]'chezmoi init'[/].\n"
    init_clone = f'To enable the [$text-primary]"{OperateBtn.init_clone_repo.initial_label}"[/] button, enter a repository address below.'


class RepositoryURLInput(VerticalGroup):

    def compose(self) -> ComposeResult:
        yield HorizontalGroup(
            Select[str].from_values(
                ["https", "ssh"],
                classes=Tcss.input_select,
                value="https",
                allow_blank=False,
                type_to_search=False,
            ),
            Input(
                placeholder="Enter repository URL",
                validate_on=["submitted"],
                validators=URL(),
                classes=Tcss.input_field,
            ),
        )


class InitNew(Vertical, AppType):

    def __init__(self) -> None:
        super().__init__(id=IDS.init.view.init_new)

    def compose(self) -> ComposeResult:
        yield MainSectionLabel(SectionLabels.init_new_repo)
        yield Static(StaticText.init_new)
        yield OperateButtons(ids=IDS.init, buttons=(OperateBtn.init_new_repo,))


class InitClone(Vertical, AppType):

    def __init__(self) -> None:
        super().__init__(id=IDS.init.view.init_clone)

    def compose(self) -> ComposeResult:
        yield MainSectionLabel(SectionLabels.init_clone_repo)
        yield SubSectionLabel(SectionLabels.init_clone_repo_url)
        yield Static(StaticText.init_clone)
        yield RepositoryURLInput()
        yield OperateButtons(
            ids=IDS.init, buttons=(OperateBtn.init_clone_repo,)
        )


class InitSwitcher(ContentSwitcher, AppType):

    def __init__(self) -> None:
        super().__init__(
            id=IDS.init.switcher.init_screen, initial=IDS.init.view.init_new
        )

    def compose(self) -> ComposeResult:
        yield InitNew()
        yield InitClone()
        yield DoctorTableView(ids=IDS.init)
        yield TemplateDataView(ids=IDS.init)

    def on_mount(self) -> None:
        if self.app.splash_data is None:
            self.notify("self.app.splash_data is None.", severity="error")
            return
        doctor_view = self.query_one(
            IDS.init.container.doctor_q, DoctorTableView
        )
        doctor_view.populate_doctor_data(
            command_result=self.app.splash_data.doctor
        )
        template_data_view = self.query_one(
            IDS.init.view.template_data_q, TemplateDataView
        )
        template_data_view.mount_template_data_output(
            self.app.splash_data.template_data
        )


class InitScreen(Screen[None], AppType):

    def __init__(self) -> None:
        super().__init__()
        self.repo_url: str | None = None
        self.valid_url: bool = False
        self.debug_log: DebugLog

    def compose(self) -> ComposeResult:
        yield CustomHeader(IDS.init)
        with Horizontal():
            yield FlatButtonsVertical(
                ids=IDS.init,
                buttons=(
                    FlatBtn.init_new,
                    FlatBtn.init_clone,
                    FlatBtn.doctor,
                    FlatBtn.template_data,
                ),
            )
            yield InitSwitcher()
        if self.app.dev_mode is True:
            yield SubSectionLabel(SectionLabels.debug_log_output)
            with Horizontal():
                yield DebugLog(ids=IDS.init)
        yield Footer(id=IDS.init.footer)

    def on_mount(self) -> None:
        self.app.update_binding_description(
            BindingAction.exit_screen, BindingDescription.exit_app
        )
        self.switcher = self.query_one(
            IDS.init.switcher.init_screen_q, InitSwitcher
        )

    @on(Button.Pressed, Tcss.flat_button.dot_prefix)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == IDS.init.flat_btn.init_new:
            self.switcher.current = IDS.init.view.init_new
        elif event.button.id == IDS.init.flat_btn.init_clone:
            self.switcher.current = IDS.init.view.init_clone
        elif event.button.id == IDS.init.flat_btn.doctor:
            self.switcher.current = IDS.init.container.doctor
        elif event.button.id == IDS.init.flat_btn.template_data:
            self.switcher.current = IDS.init.view.template_data

    @on(OperateButtonMsg)
    def handle_operate_button_pressed(self, msg: OperateButtonMsg) -> None:
        msg.stop()
        self.app.operate_data = OperateData(
            btn_enum=msg.btn_enum,
            btn_label=msg.label,
            btn_tooltip=msg.tooltip,
            repo_url=self.repo_url,
        )
        self.app.pop_screen()
        self.app.push_screen(OperateScreen())

    @on(Input.Submitted)
    def log_validation_result(self, event: Input.Submitted) -> None:
        if event.validation_result is None:
            return
        self.valid_url = event.validation_result.is_valid
        if self.valid_url is False:
            self.notify("Invalid URL entered.", severity="error")
            return
        self.notify("Valid URL entered, button enabled.")
        self.init_clone_btn = self.query_one(
            IDS.init.operate_btn.init_clone_repo_q, Button
        )
        self.init_clone_btn.disabled = False
        self.repo_url = event.value
