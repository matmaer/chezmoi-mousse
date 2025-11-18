from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.validation import URL
from textual.widgets import Button, ContentSwitcher, Footer, Input

from chezmoi_mousse import (
    AppType,
    CommandResult,
    ContainerName,
    DataTableName,
    FlatBtn,
    OperateBtn,
    SplashData,
    Tcss,
    WriteCmd,
)
from chezmoi_mousse.shared import (
    CatConfigView,
    DoctorTableView,
    FlatButtonsVertical,
    OperateButtons,
    ReactiveHeader,
    SectionLabel,
    SectionLabelText,
    SubSectionLabel,
    TemplateDataView,
)

from .tabs.logs_tab import OperateLog

__all__ = ["InitScreen"]

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds


class InitNewRepo(Vertical, AppType):

    def __init__(self, *, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.views.new_repo)
        self.repo_url: str = ""

    def compose(self) -> ComposeResult:
        yield SectionLabel("Initialize New Chezmoi Repository")
        yield SubSectionLabel(SectionLabelText.operate_output)
        yield OperateLog(ids=self.ids)

    def on_mount(self) -> None:
        operate_log = self.query_one(self.ids.loggers.operate_q, OperateLog)
        operate_log.ready_to_run(
            'Ready to run chezmoi init with default settings, see the "Cat config" tab.'
        )


class InitCloneRepo(Vertical, AppType):

    def __init__(self, *, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.views.clone_repo)
        self.repo_url: str = ""

    def compose(self) -> ComposeResult:
        yield SectionLabel("Initialize New Chezmoi Repository")
        yield SubSectionLabel("Repository URL to clone from.")
        yield Input(
            placeholder="Enter repository URL",
            validate_on=["submitted"],
            validators=URL(),
        )
        yield SubSectionLabel(SectionLabelText.operate_output)
        yield OperateLog(ids=self.ids)

    def on_mount(self) -> None:
        operate_log = self.query_one(self.ids.loggers.operate_q, OperateLog)
        operate_log.ready_to_run(
            "Ready to run chezmoi init cloning from the remote repository."
        )

    @on(Input.Submitted)
    def log_invalid_reasons(self, event: Input.Submitted) -> None:
        operate_log = self.query_one(OperateLog)
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
            self.app.notify(f"Will submit repository URL: {self.repo_url}")


class InitSwitcher(ContentSwitcher):

    def __init__(self, *, ids: "CanvasIds", splash_data: "SplashData") -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.container_id(name=ContainerName.init_screen_switcher),
            initial=self.ids.views.clone_repo,
        )
        self.splash_data = splash_data
        self.doctor_table_qid = ids.datatable_id(
            "#", data_table_name=DataTableName.doctor_table
        )

    def compose(self) -> ComposeResult:
        yield InitCloneRepo(ids=self.ids)
        yield InitNewRepo(ids=self.ids)
        yield DoctorTableView(ids=self.ids)
        yield CatConfigView(ids=self.ids)
        yield TemplateDataView(ids=self.ids)

    def on_mount(self) -> None:
        doctor_view = self.query_one(self.ids.views.doctor_q, DoctorTableView)
        doctor_view.populate_doctor_data(
            command_result=self.splash_data.doctor
        )
        cat_config = self.query_one(self.ids.views.cat_config_q, CatConfigView)
        cat_config.mount_cat_config_output(self.splash_data.cat_config)
        template_data_view = self.query_one(
            self.ids.views.template_data_q, TemplateDataView
        )
        template_data_view.mount_template_data_output(
            self.splash_data.template_data
        )


class InitScreen(Screen[CommandResult | None], AppType):

    BINDINGS = [
        Binding(
            key="escape",
            action="exit_operation",
            description="Press the escape key to exit",
            show=True,
        )
    ]

    def __init__(self, *, ids: "CanvasIds", splash_data: "SplashData") -> None:
        super().__init__()

        self.ids = ids
        self.container_id = ids.container_id(name=ContainerName.left_side)
        self.splash_data = splash_data
        self.command_result: CommandResult | None = None

        self.operate_btn_id = ids.button_id(btn=OperateBtn.init_new_repo)
        self.operate_btn_qid = ids.button_id("#", btn=OperateBtn.init_new_repo)
        self.exit_btn_id = ids.button_id(btn=OperateBtn.exit_button)
        self.exit_btn_qid = ids.button_id("#", btn=OperateBtn.exit_button)

    def compose(self) -> ComposeResult:
        yield ReactiveHeader(self.app.init_screen_ids)
        with Horizontal(id=self.ids.canvas_container_id):
            yield FlatButtonsVertical(
                ids=self.ids,
                buttons=(
                    FlatBtn.init_clone_repo,
                    FlatBtn.init_new_repo,
                    FlatBtn.doctor,
                    FlatBtn.cat_config,
                    FlatBtn.template_data,
                ),
            )
            yield InitSwitcher(ids=self.ids, splash_data=self.splash_data)
        yield OperateButtons(
            ids=self.ids,
            buttons=(OperateBtn.init_new_repo, OperateBtn.exit_button),
        )
        yield Footer()

    def on_mount(self) -> None:
        op_btn = self.query_one(self.operate_btn_qid, Button)
        op_btn.disabled = False
        exit_btn = self.query_one(self.exit_btn_qid, Button)
        exit_btn.disabled = False
        exit_btn.tooltip = None

    def post_operate_ui_update(self) -> None:
        operate_button = self.query_one(self.operate_btn_qid, Button)
        operate_button.disabled = True
        operate_button.tooltip = None

        operate_exit_button = self.query_one(self.exit_btn_qid, Button)
        operate_exit_button.label = OperateBtn.exit_button.close_button_label

        # output_log = self.query_one(self.ids.views.operate_log_q, OperateLog)
        # if self.operate_data.command_result is not None:
        #     output_log.log_cmd_results(self.operate_data.command_result)
        # else:
        #     output_log.error("Command result is None, cannot log output.")

    @on(Button.Pressed, Tcss.flat_button.value)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_one(
            self.ids.container_id(
                "#", name=ContainerName.init_screen_switcher
            ),
            ContentSwitcher,
        )
        if event.button.id == self.ids.view_btn.new_repo:
            switcher.current = self.ids.views.new_repo
        elif event.button.id == self.ids.view_btn.clone_repo:
            switcher.current = self.ids.views.clone_repo
        elif event.button.id == self.ids.view_btn.doctor:
            switcher.current = self.ids.views.doctor
        elif event.button.id == self.ids.view_btn.cat_config:
            switcher.current = self.ids.views.cat_config
        elif event.button.id == self.ids.view_btn.template_data:
            switcher.current = self.ids.views.template_data

    @on(Button.Pressed, Tcss.operate_button.value)
    def handle_operate_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == self.exit_btn_id:
            self.dismiss(self.command_result)
        else:
            self.command_result = self.app.chezmoi.perform(
                WriteCmd.add, dry_run=self.app.changes_enabled
            )
            self.post_operate_ui_update()

    def action_exit_operation(self) -> None:
        self.dismiss(self.command_result)
