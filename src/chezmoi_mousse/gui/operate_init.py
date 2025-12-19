from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import HorizontalGroup, VerticalGroup
from textual.screen import Screen
from textual.validation import URL
from textual.widgets import (
    Button,
    Footer,
    Input,
    Label,
    Select,
    Static,
    Switch,
)

from chezmoi_mousse import (
    IDS_OPERATE_INIT,
    AppType,
    BindingAction,
    BindingDescription,
    LinkBtn,
    OperateBtn,
    OperateStrings,
    SectionLabels,
    Switches,
    Tcss,
    WriteCmd,
)
from chezmoi_mousse.shared import (
    SSHSCP,
    CustomCollapsible,
    CustomHeader,
    DebugLog,
    DoctorTable,
    FlatLink,
    InitCompletedMsg,
    OperateButtons,
    OperateLog,
    PrettyTemplateData,
    SwitchWithLabel,
)

__all__ = ["OperateInit"]


class InputURL(Input):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Enter a repo URL",
            validate_on=["submitted"],
            validators=URL(),
            classes=Tcss.input_field,
        )


class InputSSH(Input):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Enter an SSH address",
            validate_on=["submitted"],
            validators=SSHSCP(),
            classes=Tcss.input_field,
        )


class InputGuessURL(HorizontalGroup):

    def compose(self) -> ComposeResult:
        yield Input(
            placeholder="Let chezmoi guess the repo URL",
            classes=Tcss.input_field,
        )
        yield FlatLink(ids=IDS_OPERATE_INIT, link_enum=LinkBtn.chezmoi_guess)


class InputGuessSSH(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield Input(
            placeholder="Let chezmoi guess the SSH repo address",
            classes=Tcss.input_field,
        )
        yield FlatLink(ids=IDS_OPERATE_INIT, link_enum=LinkBtn.chezmoi_guess)


class InputInitCloneRepo(HorizontalGroup):

    def __init__(self) -> None:
        super().__init__(id=IDS_OPERATE_INIT.container.repo_input)

    def compose(self) -> ComposeResult:
        yield Select(
            options=[
                ("https", "https"),
                ("ssh", "ssh"),
                ("guess url", "guess url"),
                ("guess ssh", "guess ssh"),
            ],
            value="https",
            classes=Tcss.input_select,
            allow_blank=False,
            type_to_search=False,
        )
        yield InputURL()
        yield InputSSH()
        yield InputGuessURL()
        yield InputGuessSSH()

    def on_mount(self) -> None:
        self.query_exactly_one(InputSSH).display = False
        self.query_exactly_one(InputGuessURL).display = False
        self.query_exactly_one(InputGuessSSH).display = False


class InitCollapsibles(VerticalGroup, AppType):
    def __init__(self) -> None:
        super().__init__()
        if self.app.splash_data is None:
            raise ValueError("self.app.splash_data is None in OperateScreen")
        self.splash_data = self.app.splash_data

    def compose(self) -> ComposeResult:
        yield Label(
            SectionLabels.pre_init_cmd_output, classes=Tcss.sub_section_label
        )
        yield CustomCollapsible(
            DoctorTable(
                ids=IDS_OPERATE_INIT, doctor_data=self.splash_data.doctor
            ),
            title="Doctor Output",
        )
        yield CustomCollapsible(
            PrettyTemplateData(self.splash_data.template_data),
            title="Template Data Output",
        )


class OperateInit(Screen[None], AppType):

    BINDINGS = [
        Binding(
            key="escape",
            action=BindingAction.exit_screen,
            description=BindingDescription.exit_app,
        )
    ]

    def __init__(self) -> None:
        super().__init__()
        if self.app.operate_data is None:
            raise ValueError("self.app.operate_data is None in OperateScreen")
        self.op_data = self.app.operate_data
        self.ids = IDS_OPERATE_INIT
        self.guess_https: bool | None = None
        self.guess_ssh: bool | None = None
        self.init_cmd: WriteCmd | None = None
        self.repo_arg: str | None = None
        self.valid_url: bool = False
        self.init_clone_https_static_text = "\n".join(
            [OperateStrings.https_url.value, OperateStrings.pat_info.value]
        )
        self.init_clone_ssh_static_text = OperateStrings.ssh_select
        self.init_clone_guess_https_static_text = OperateStrings.guess_https
        self.init_clone_guess_ssh_static_text = OperateStrings.guess_ssh

    def compose(self) -> ComposeResult:
        yield CustomHeader(self.ids)
        yield Static(
            id=self.ids.static.operate_info, classes=Tcss.operate_info
        )
        yield VerticalGroup(
            HorizontalGroup(
                Label(
                    SectionLabels.init_new_repo,
                    classes=Tcss.main_section_label,
                ),
                SwitchWithLabel(
                    ids=self.ids, switch_enum=Switches.init_repo_switch
                ),
            ),
            Static(id=self.ids.static.init_info),
            InputInitCloneRepo(),
            InitCollapsibles(),
            id=self.ids.container.pre_operate,
        )
        with VerticalGroup(id=self.ids.container.post_operate):
            yield Label(
                SectionLabels.operate_output, classes=Tcss.main_section_label
            )
            yield OperateLog(ids=self.ids)
        if self.app.dev_mode:
            yield Label(SectionLabels.debug_log_output)
            yield DebugLog(self.ids)
        yield OperateButtons(
            ids=self.ids,
            buttons=(self.op_data.btn_enum, OperateBtn.operate_exit),
        )
        yield Footer(id=self.ids.footer)

    def on_mount(self) -> None:
        self.post_op_container = self.query_one(
            self.ids.container.post_operate_q, VerticalGroup
        )
        self.post_op_container.display = False
        self.pre_op_container = self.query_one(
            self.ids.container.pre_operate_q, VerticalGroup
        )
        self.operate_info = self.query_one(
            self.ids.static.operate_info_q, Static
        )
        self.op_btn = self.query_one(
            self.ids.operate_button_id("#", btn=self.op_data.btn_enum), Button
        )
        self.op_btn.label = self.op_data.btn_label
        self.op_btn.tooltip = self.op_data.btn_tooltip
        self.exit_btn = self.query_one(
            self.ids.operate_button_id("#", btn=OperateBtn.operate_exit),
            Button,
        )
        self.query_exactly_one(SwitchWithLabel).add_class(Tcss.single_switch)
        self.repo_input = self.query_one(
            self.ids.container.repo_input_q, InputInitCloneRepo
        )
        self.repo_input.display = False
        self.init_static = self.query_one(self.ids.static.init_info_q, Static)
        self.exit_btn.label = OperateBtn.operate_exit.exit_app_label
        self.guess_docs_link = self.query_one(
            self.ids.link_button_id("#", btn=LinkBtn.chezmoi_guess), FlatLink
        )
        self.guess_docs_link.display = False
        self.input_url = self.query_exactly_one(InputURL)
        self.input_ssh = self.query_exactly_one(InputSSH)
        self.input_guess_url = self.query_exactly_one(InputGuessURL)
        self.input_guess_ssh = self.query_exactly_one(InputGuessSSH)
        self.update_operate_info()
        self.update_static_text()

    def update_operate_info(self) -> None:
        lines_to_write: list[str] = []
        if self.op_btn.label == OperateBtn.init_repo.init_clone_label:
            lines_to_write.append(OperateStrings.init_clone_operate_info)
        else:
            lines_to_write.append(OperateStrings.init_new_operate_info)
        if self.app.changes_enabled is True:
            lines_to_write.append(OperateStrings.changes_enabled)
        else:
            lines_to_write.append(OperateStrings.changes_disabled)
        self.operate_info.update("\n".join(lines_to_write))

    def update_static_text(self) -> None:
        switch_state = self.query_exactly_one(Switch).value
        if switch_state is False:
            self.init_static.update(OperateStrings.init_new.value)
            return
        current_select = self.repo_input.query_exactly_one(Select[str]).value
        if current_select == "https":
            self.init_static.update(self.init_clone_https_static_text)
        elif current_select == "ssh":
            self.init_static.update(self.init_clone_ssh_static_text)
        elif current_select == "guess url":
            self.init_static.update(self.init_clone_guess_https_static_text)
        elif current_select == "guess ssh":
            self.init_static.update(self.init_clone_guess_ssh_static_text)

    @on(Switch.Changed)
    def handle_switch_state(self, event: Switch.Changed) -> None:
        if event.value is True:
            self.repo_input.display = True
            self.op_btn.label = OperateBtn.init_repo.init_clone_label
        elif event.value is False:
            self.repo_input.display = False
            self.op_btn.label = OperateBtn.init_repo.init_new_label
        self.update_static_text()
        self.update_operate_info()

    @on(Input.Submitted)
    def handle_validation(self, event: Input.Submitted) -> None:
        event.stop()
        if event.validation_result is None:
            self.notify("No input provided.", severity="error")
            return
        self.valid_url = event.validation_result.is_valid
        if self.valid_url is False:
            self.notify("Invalid URL entered.", severity="error")
            return
        self.repo_url = event.value
        self.notify("Valid URL entered, init clone enabled.")
        self.op_btn.tooltip = OperateBtn.init_repo.enabled_tooltip

    @on(Button.Pressed, Tcss.operate_button.dot_prefix)
    def handle_operate_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == OperateBtn.operate_exit.exit_app_label:
            self.app.exit()
        elif event.button.label == OperateBtn.operate_exit.reload_label:
            self.app.post_message(InitCompletedMsg())
            self.dismiss()
        else:
            self.run_operate_command()

    def run_operate_command(self) -> None:
        if self.op_btn.label == OperateBtn.init_repo.init_new_label:
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.init_new, changes_enabled=self.app.changes_enabled
            )
        elif self.op_btn.label == OperateBtn.init_repo.init_clone_label:
            if self.valid_url is True:
                self.app.operate_cmd_result = self.app.chezmoi.perform(
                    WriteCmd.init_no_guess,
                    init_repo_arg=self.repo_arg,
                    changes_enabled=self.app.changes_enabled,
                )
            elif self.guess_https is True:
                self.app.operate_cmd_result = self.app.chezmoi.perform(
                    WriteCmd.init_guess_https,
                    init_repo_arg=self.repo_arg,
                    changes_enabled=self.app.changes_enabled,
                )
            elif self.guess_ssh is True:
                self.app.operate_cmd_result = self.app.chezmoi.perform(
                    WriteCmd.init_guess_ssh,
                    init_repo_arg=self.repo_arg,
                    changes_enabled=self.app.changes_enabled,
                )
        if self.app.operate_cmd_result is None:
            raise ValueError(
                "self.app.operate_cmd_result is None after running command"
            )
        self.pre_op_container.display = False
        self.post_op_container.display = True
        output_log = self.query_one(self.ids.logger.operate_q, OperateLog)
        output_log.log_cmd_results(self.app.operate_cmd_result)
        if self.app.changes_enabled is False:
            self.op_btn.disabled = True
            self.op_btn.tooltip = None
            self.exit_btn.label = OperateBtn.operate_exit.reload_label
            new_description = BindingDescription.reload
            self.app.update_binding_description(
                BindingAction.exit_screen, new_description
            )

    @on(Select.Changed)
    def hanle_selection_change(self, event: Select.Changed) -> None:
        if event.value == "https":
            self.guess_docs_link.display = False
            self.input_url.display = True
            self.input_ssh.display = False
            self.input_guess_url.display = False
            self.input_guess_ssh.display = False
        elif event.value == "ssh":
            self.guess_docs_link.display = False
            self.input_url.display = False
            self.input_ssh.display = True
            self.input_guess_url.display = False
            self.input_guess_ssh.display = False
        elif event.value == "guess url":
            self.input_url.display = False
            self.input_ssh.display = False
            self.input_guess_url.display = True
            self.input_guess_ssh.display = False
            self.guess_docs_link.display = True
        elif event.value == "guess ssh":
            self.input_url.display = False
            self.input_ssh.display = False
            self.input_guess_url.display = False
            self.input_guess_ssh.display = True
            self.guess_docs_link.display = True
        self.update_static_text()

    def action_exit_screen(self) -> None:
        if (
            self.app.operate_cmd_result is None
            or self.app.operate_cmd_result.dry_run is True
        ):
            self.app.exit()
        else:
            self.screen.dismiss()
