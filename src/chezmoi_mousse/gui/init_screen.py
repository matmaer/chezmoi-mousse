import dataclasses
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
    CommandResult,
    FlatBtn,
    LogText,
    OperateBtn,
    SectionLabels,
    Tcss,
    WriteCmd,
)
from chezmoi_mousse.shared import (
    CatConfigView,
    CustomHeader,
    DebugLog,
    DoctorTableView,
    FlatButtonsVertical,
    MainSectionLabel,
    OperateButtons,
    OperateLog,
    SubSectionLabel,
    TemplateDataView,
)

__all__ = ["InitScreen"]

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds, SplashData


class InitNewRepo(Vertical, AppType):

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.view.new_repo)

    def compose(self) -> ComposeResult:
        yield MainSectionLabel(SectionLabels.init_new_repo)
        yield OperateButtons(
            ids=self.ids,
            buttons=(OperateBtn.init_new_repo, OperateBtn.init_exit),
        )


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


class InitCloneRepo(Vertical, AppType):

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.view.clone_repo)

    def compose(self) -> ComposeResult:
        yield MainSectionLabel(SectionLabels.init_clone_repo)
        yield SubSectionLabel(SectionLabels.init_clone_repo_url)
        yield RepositoryURLInput()
        yield OperateButtons(
            ids=self.ids,
            buttons=(OperateBtn.init_clone_repo, OperateBtn.init_exit),
        )


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


class InitScreen(Screen["CommandResult | None"], AppType):

    BINDINGS = [
        Binding(
            key="escape",
            action="exit_operation",
            description=BindingDescription.exit_app,
            show=True,
        )
    ]

    def __init__(self, *, ids: "AppIds", splash_data: "SplashData") -> None:
        super().__init__()
        self.ids = ids
        self.splash_data = splash_data
        self.command_result: CommandResult | None = None
        self.repo_url: str | None = None
        self.valid_url: bool = False
        self.debug_log: DebugLog
        self.operate_log: OperateLog

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
            yield InitSwitcher(ids=self.ids, splash_data=self.splash_data)
        yield SubSectionLabel(SectionLabels.operate_output)
        if self.app.dev_mode is True:
            with Horizontal():
                yield OperateLog(ids=self.ids)
                yield DebugLog(ids=self.ids)
        else:
            yield OperateLog(ids=self.ids)
        yield Footer(id=self.ids.footer)

    def on_mount(self) -> None:
        self.operate_log = self.query_one(
            self.ids.logger.operate_q, OperateLog
        )
        self.operate_log.ready_to_run(LogText.operate_log_initialized)
        if self.app.dev_mode:
            self.operate_log.info(LogText.dev_mode_enabled)
            self.debug_log = self.query_one(self.ids.logger.debug_q, DebugLog)
            self.debug_log.ready_to_run(LogText.debug_log_initialized)

    def log_command_and_update_buttons(self) -> None:
        if self.command_result is None:
            # this should not happen
            self.notify("Operation returned None.", severity="error")
            return
        # Log results
        self.operate_log.log_cmd_results(self.command_result)
        if self.command_result.returncode != 0:
            self.notify("Operation failed.", severity="error")
            return
        # Update buttons
        init_new_btn = self.query_one(
            self.ids.operate_btn.init_new_repo_q, Button
        )
        init_new_btn.disabled = True
        init_new_btn.tooltip = None
        init_clone_btn = self.query_one(
            self.ids.operate_btn.init_clone_repo_q, Button
        )
        init_clone_btn.disabled = True
        init_clone_btn.tooltip = None
        exit_button = self.query_one(self.ids.operate_btn.init_exit_q, Button)
        exit_button.label = OperateBtn.init_exit.close_label
        exit_button.tooltip = OperateBtn.init_exit.close_tooltip

    def perform_init_new(self) -> None:
        # Run command
        self.command_result = self.app.chezmoi.perform(
            WriteCmd.init, dry_run=self.app.changes_enabled
        )
        self.log_command_and_update_buttons()

    def perform_init_clone(self, repo_url: str | None = None) -> None:
        # Run command
        self.command_result = self.app.chezmoi.perform(
            WriteCmd.init, dry_run=self.app.changes_enabled, repo_url=repo_url
        )
        self.log_command_and_update_buttons()

    @on(Button.Pressed, Tcss.flat_button.dot_prefix)
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

    def update_bindings(self, operate_button: OperateBtn) -> None:
        if self.command_result is None:
            return
        if operate_button == OperateBtn.init_clone_repo and (
            self.repo_url is None or self.valid_url is not True
        ):
            return
        new_description = (
            BindingDescription.reload
            if self.command_result.returncode == 0
            else BindingDescription.exit_app
        )
        for key, binding in self._bindings:
            if binding.action == "exit_operation":
                updated_binding = dataclasses.replace(
                    binding, description=new_description
                )
                if key in self._bindings.key_to_bindings:
                    bindings_list = self._bindings.key_to_bindings[key]
                    for i, b in enumerate(bindings_list):
                        if b.action == "exit_operation":
                            bindings_list[i] = updated_binding
                            break
                break
            self.refresh_bindings()

    @on(Button.Pressed, Tcss.operate_button.dot_prefix)
    async def handle_operate_button_pressed(
        self, event: Button.Pressed
    ) -> None:
        event.stop()
        if event.button.id == self.ids.operate_btn.init_exit:
            # TODO: check network connectivity before proceeding
            self.dismiss(self.command_result)
        elif event.button.id == self.ids.operate_btn.init_new_repo:
            self.perform_init_new()
            self.update_bindings(operate_button=OperateBtn.init_new_repo)
        elif event.button.id == self.ids.operate_btn.init_clone_repo:
            # Submit the input, which triggers validation and logs it.
            input_widget = self.query_exactly_one(Input)
            await input_widget.action_submit()
            if self.valid_url is not True:
                self.notify("Repository URL is invalid.", severity="error")
            if self.repo_url is not None:
                self.perform_init_clone(repo_url=self.repo_url)
                self.update_bindings(operate_button=OperateBtn.init_clone_repo)

    @on(Input.Submitted)
    def log_validation_result(self, event: Input.Submitted) -> None:
        if event.validation_result is None:
            return
        self.debug_log.info(f"event.value: {event.value!r}")
        self.debug_log.info(f"is space: {event.value.isspace()}")
        self.debug_log.list_attr(event.value)
        self.valid_url = event.validation_result.is_valid
        if not event.validation_result.is_valid:
            self.operate_log.info(
                "\n".join(event.validation_result.failure_descriptions)
            )
            return
        else:
            if event.value == "":
                self.operate_log.warning("No URL entered.")
                self.repo_url = None
            else:
                self.repo_url = event.value
                self.operate_log.success(f"Valid URL entered: {self.repo_url}")

    def action_exit_operation(self) -> None:
        if (
            self.command_result is not None
            and self.command_result.returncode == 0
        ):
            self.dismiss(self.command_result)
        else:
            self.app.exit()
