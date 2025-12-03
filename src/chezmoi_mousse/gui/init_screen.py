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
    SCREEN_IDS,
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
    CatConfigView,
    CustomHeader,
    DebugLog,
    DoctorTableView,
    FlatButtonsVertical,
    MainSectionLabel,
    OperateButtons,
    SubSectionLabel,
    TemplateDataView,
)

from .operate import OperateScreen

__all__ = ["InitScreen"]


class StaticText(StrEnum):
    init_new = f"Initialize a new chezmoi repository in your home directory, check the [$text-primary]{FlatBtn.cat_config}[/] section for the default settings in use.\nClick the [$text-primary]{OperateBtn.init_new_repo.initial_label}[/] button below to run [$text-success]'chezmoi init'[/].\n"
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
        super().__init__(id=SCREEN_IDS.init.view.init_new)

    def compose(self) -> ComposeResult:
        yield MainSectionLabel(SectionLabels.init_new_repo)
        yield Static(StaticText.init_new)
        yield OperateButtons(
            ids=SCREEN_IDS.init, buttons=(OperateBtn.init_new_repo,)
        )


class InitClone(Vertical, AppType):

    def __init__(self) -> None:
        super().__init__(id=SCREEN_IDS.init.view.init_clone)

    def compose(self) -> ComposeResult:
        yield MainSectionLabel(SectionLabels.init_clone_repo)
        yield SubSectionLabel(SectionLabels.init_clone_repo_url)
        yield Static(StaticText.init_clone)
        yield RepositoryURLInput()
        yield OperateButtons(
            ids=SCREEN_IDS.init, buttons=(OperateBtn.init_clone_repo,)
        )


class InitSwitcher(ContentSwitcher, AppType):

    def __init__(self) -> None:
        super().__init__(
            id=SCREEN_IDS.init.switcher.init_screen,
            initial=SCREEN_IDS.init.view.init_new,
        )

    def compose(self) -> ComposeResult:
        yield InitNew()
        yield InitClone()
        yield DoctorTableView(ids=SCREEN_IDS.init)
        yield CatConfigView(ids=SCREEN_IDS.init)
        yield TemplateDataView(ids=SCREEN_IDS.init)

    def on_mount(self) -> None:
        if self.app.splash_data is None:
            self.notify("self.app.splash_data is None.", severity="error")
            return
        doctor_view = self.query_one(
            SCREEN_IDS.init.container.doctor_q, DoctorTableView
        )
        doctor_view.populate_doctor_data(
            command_result=self.app.splash_data.doctor
        )
        cat_config = self.query_one(
            SCREEN_IDS.init.view.cat_config_q, CatConfigView
        )
        cat_config.mount_cat_config_output(self.app.splash_data.cat_config)
        template_data_view = self.query_one(
            SCREEN_IDS.init.view.template_data_q, TemplateDataView
        )
        template_data_view.mount_template_data_output(
            self.app.splash_data.template_data
        )


class InitScreen(Screen["OperateData"], AppType):

    def __init__(self) -> None:
        super().__init__()
        self.repo_url: str | None = None
        self.valid_url: bool = False
        self.debug_log: DebugLog

    def compose(self) -> ComposeResult:
        yield CustomHeader(SCREEN_IDS.init)
        with Horizontal():
            yield FlatButtonsVertical(
                ids=SCREEN_IDS.init,
                buttons=(
                    FlatBtn.init_new,
                    FlatBtn.init_clone,
                    FlatBtn.doctor,
                    FlatBtn.cat_config,
                    FlatBtn.template_data,
                ),
            )
            yield InitSwitcher()
        if self.app.dev_mode is True:
            yield SubSectionLabel(SectionLabels.debug_log_output)
            with Horizontal():
                yield DebugLog(ids=SCREEN_IDS.init)
        yield Footer(id=SCREEN_IDS.init.footer)

    def on_mount(self) -> None:
        self.app.operate_data = None
        self.init_clone_btn = self.query_one(
            SCREEN_IDS.init.operate_btn.init_clone_repo_q, Button
        )
        self.init_clone_btn.disabled = True
        self.app.update_binding_description(
            BindingAction.exit_screen, BindingDescription.exit_app
        )

    @on(Button.Pressed, Tcss.flat_button.dot_prefix)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_one(
            SCREEN_IDS.init.switcher.init_screen_q, ContentSwitcher
        )
        if event.button.id == SCREEN_IDS.init.flat_btn.init_new:
            switcher.current = SCREEN_IDS.init.view.init_new
        elif event.button.id == SCREEN_IDS.init.flat_btn.init_clone:
            switcher.current = SCREEN_IDS.init.view.init_clone
        elif event.button.id == SCREEN_IDS.init.flat_btn.doctor:
            switcher.current = SCREEN_IDS.init.container.doctor
        elif event.button.id == SCREEN_IDS.init.flat_btn.cat_config:
            switcher.current = SCREEN_IDS.init.view.cat_config
        elif event.button.id == SCREEN_IDS.init.flat_btn.template_data:
            switcher.current = SCREEN_IDS.init.view.template_data

    @on(Button.Pressed, Tcss.operate_button.dot_prefix)
    def handle_operate_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        operate_data = OperateData(operate_btn=OperateBtn.init_new_repo)
        if event.button.id == SCREEN_IDS.init.operate_btn.init_clone_repo:
            operate_data = OperateData(
                operate_btn=OperateBtn.init_clone_repo, repo_url=self.repo_url
            )
        self.app.pop_screen()
        self.app.push_screen(OperateScreen(operate_data=operate_data))

    @on(Input.Submitted)
    def log_validation_result(self, event: Input.Submitted) -> None:
        if event.validation_result is None:
            return
        self.valid_url = event.validation_result.is_valid
        if not self.valid_url:
            self.notify("Invalid URL entered.", severity="error")
            return
        self.notify("Valid URL entered, button enabled.")
        self.init_clone_btn.disabled = False
        self.repo_url = event.value
