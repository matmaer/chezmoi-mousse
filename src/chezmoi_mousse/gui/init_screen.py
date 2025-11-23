from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import (
    Horizontal,
    HorizontalGroup,
    Vertical,
    VerticalGroup,
)
from textual.screen import Screen
from textual.validation import URL
from textual.widgets import Button, ContentSwitcher, Footer, Input, Select

from chezmoi_mousse import (
    AppType,
    BindingDescription,
    FlatBtn,
    OperateBtn,
    Tcss,
    WriteCmd,
)
from chezmoi_mousse.shared import (
    CatConfigView,
    CustomHeader,
    DoctorTableView,
    FlatButtonsVertical,
    MainSectionLabel,
    OperateButtons,
    SectionLabelText,
    SubSectionLabel,
    TemplateDataView,
)

from .tabs.logs_tab import OperateLog

__all__ = ["InitScreen"]

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds, SplashData


class InitNewRepo(Vertical, AppType):

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.view.new_repo)
        self.repo_url: str = ""

    def compose(self) -> ComposeResult:
        yield MainSectionLabel("Initialize New Chezmoi Repository")
        yield SubSectionLabel(SectionLabelText.operate_output)
        yield OperateLog(ids=self.ids)

    def on_mount(self) -> None:
        operate_log = self.query_one(self.ids.logger.operate_q, OperateLog)
        operate_log.ready_to_run(
            'Ready to run chezmoi init with default settings, see the "Cat config" tab.'
        )


class RepositoryURLInput(VerticalGroup):

    def compose(self) -> ComposeResult:
        yield HorizontalGroup(
            Select[str].from_values(
                ["https", "ssh"],
                classes=Tcss.input_select.name,
                value="https",
                allow_blank=False,
                type_to_search=False,
            ),
            Input(
                placeholder="Enter repository URL",
                validate_on=["submitted"],
                validators=URL(),
                classes=Tcss.input_field.name,
            ),
        )


class InitCloneRepo(Vertical, AppType):

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.view.clone_repo)
        self.repo_url: str = ""

    def compose(self) -> ComposeResult:
        yield MainSectionLabel("Initialize New Chezmoi Repository")
        yield SubSectionLabel("Repository URL to clone from.")
        yield RepositoryURLInput()
        yield SubSectionLabel(SectionLabelText.operate_output)
        yield OperateLog(ids=self.ids)

    def on_mount(self) -> None:
        operate_log = self.query_one(self.ids.logger.operate_q, OperateLog)
        operate_log.ready_to_run(
            "Ready to run chezmoi init cloning from the remote repository."
        )

    @on(Input.Submitted)
    def log_invalid_reasons(self, event: Input.Submitted) -> None:
        operate_log = self.query_exactly_one(OperateLog)
        if (
            event.validation_result is not None
            and not event.validation_result.is_valid
        ):
            text_lines: str = "\n".join(
                event.validation_result.failure_descriptions
            )
            operate_log.info(text_lines)
        else:
            self.repo_url = event.value
            operate_log.success(f"Valid URL entered: {self.repo_url}")


class InitSwitcher(ContentSwitcher):

    def __init__(self, *, ids: "AppIds", splash_data: "SplashData") -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.switcher.init_screen, initial=self.ids.view.clone_repo
        )
        self.splash_data = splash_data

    def compose(self) -> ComposeResult:
        yield InitCloneRepo(ids=self.ids)
        yield InitNewRepo(ids=self.ids)
        yield DoctorTableView(ids=self.ids)
        yield CatConfigView(ids=self.ids)
        yield TemplateDataView(ids=self.ids)

    def on_mount(self) -> None:
        doctor_view = self.query_one(
            self.ids.container.doctor_q, DoctorTableView
        )
        doctor_view.populate_doctor_data(
            command_result=self.splash_data.doctor
        )
        cat_config = self.query_one(self.ids.view.cat_config_q, CatConfigView)
        cat_config.mount_cat_config_output(self.splash_data.cat_config)
        template_data_view = self.query_one(
            self.ids.view.template_data_q, TemplateDataView
        )
        template_data_view.mount_template_data_output(
            self.splash_data.template_data
        )


class InitScreen(Screen["SplashData | None"], AppType):

    BINDINGS = [
        Binding(
            key="escape",
            action="exit_operation",
            description=BindingDescription.back,
            show=True,
        )
    ]

    def __init__(self, *, ids: "AppIds", splash_data: "SplashData") -> None:
        self.ids = ids
        super().__init__()

        self.splash_data = splash_data
        self.operate_btn_id = ids.button_id(btn=OperateBtn.init_new_repo)
        self.operate_btn_qid = ids.button_id("#", btn=OperateBtn.init_new_repo)
        self.exit_btn_id = ids.button_id(btn=OperateBtn.exit_button)
        self.exit_btn_qid = ids.button_id("#", btn=OperateBtn.exit_button)

    def compose(self) -> ComposeResult:
        yield CustomHeader(self.ids)
        with Horizontal():
            yield FlatButtonsVertical(
                ids=self.ids,
                buttons=(
                    FlatBtn.clone_repo,
                    FlatBtn.new_repo,
                    FlatBtn.doctor,
                    FlatBtn.cat_config,
                    FlatBtn.template_data,
                ),
            )
            with Vertical():
                yield InitSwitcher(ids=self.ids, splash_data=self.splash_data)
                yield OperateButtons(
                    ids=self.ids,
                    buttons=(OperateBtn.init_new_repo, OperateBtn.exit_button),
                )
        yield Footer(id=self.ids.footer)

    def on_mount(self) -> None:
        op_btn = self.query_one(self.operate_btn_qid, Button)
        op_btn.disabled = False
        exit_btn = self.query_one(self.exit_btn_qid, Button)
        exit_btn.disabled = False

    def perform_init_command(self) -> None:
        # Run command
        self.splash_data.init = self.app.chezmoi.perform(
            WriteCmd.init, dry_run=self.app.changes_enabled
        )
        # Log results
        output_log = self.query_one(self.ids.logger.operate_q, OperateLog)
        output_log.log_cmd_results(self.splash_data.init)
        # Update buttons
        operate_button = self.query_one(self.operate_btn_qid, Button)
        operate_button.disabled = True
        operate_button.tooltip = None
        exit_button = self.query_one(self.exit_btn_qid, Button)
        exit_button.label = OperateBtn.exit_button.close_label

    @on(Button.Pressed, Tcss.flat_button.value)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_one(
            self.ids.switcher.init_screen_q, ContentSwitcher
        )
        if event.button.id == self.ids.flat_btn.new_repo:
            switcher.current = self.ids.view.new_repo
        elif event.button.id == self.ids.flat_btn.clone_repo:
            switcher.current = self.ids.view.clone_repo
        elif event.button.id == self.ids.flat_btn.doctor:
            switcher.current = self.ids.container.doctor
        elif event.button.id == self.ids.flat_btn.cat_config:
            switcher.current = self.ids.view.cat_config
        elif event.button.id == self.ids.flat_btn.template_data:
            switcher.current = self.ids.view.template_data

    @on(Button.Pressed, Tcss.operate_button.value)
    def handle_operate_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == self.exit_btn_id:
            if event.button.label == OperateBtn.exit_button.close_label:
                self.dismiss(self.splash_data)
            elif event.button.label == OperateBtn.exit_button.cancel_label:
                return None
        else:
            self.perform_init_command()

    def action_exit_operation(self) -> None:
        self.dismiss(self.splash_data)
