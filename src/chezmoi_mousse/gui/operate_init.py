from enum import StrEnum

from textual import on
from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup
from textual.validation import URL
from textual.widgets import Button, Input, Label, Select, Static, Switch

from chezmoi_mousse import (
    IDS,
    AppType,
    LinkBtn,
    OperateBtn,
    SectionLabels,
    Switches,
    Tcss,
    WriteCmd,
)
from chezmoi_mousse.shared import (
    SSHSCP,
    CustomCollapsible,
    DoctorTable,
    FlatLink,
    InitCompletedMsg,
    OperateScreenBase,
    PrettyTemplateData,
    SwitchWithLabel,
)

__all__ = ["InitScreen"]


class InitStaticText(StrEnum):
    init_clone = f"Click the [$primary-lighten-3 on $surface-lighten-1] {OperateBtn.init_repo.init_clone_label} [/] button to initialize a new chezmoi repository.\n"
    init_new = f"Click the [$primary-lighten-3 on $surface-lighten-1] {OperateBtn.init_repo.initial_label} [/] button to initialize a new chezmoi repository."
    init_switch_on = f"Switch [$foreground-darken-1 on $surface-lighten-1] {Switches.init_repo_switch.label} [/] ON to clone an existing repository.\n"
    guess_https = "Let chezmoi guess the best URL to clone from."
    guess_ssh = (
        "Let chezmoi guess the best ssh scp-style address to clone from."
    )
    https_url = "Enter a complete URL, e.g., [$text-primary]https://github.com/user/repo.git[/]."
    pat_info = "If you have a PAT, make sure to include it in the URL, for example: [$text-primary]https://username:ghp_123456789abcdef@github.com/username/my-dotfiles.git[/] and delete the PAT after use."
    ssh_select = "Enter an SSH SCP-style URL, e.g., [$text-primary]git@github.com:user/repo.git[/]. If your dotfiles repository is private, make sure you have your SSH key pair set up before using this option."


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
        yield FlatLink(ids=IDS.operate, link_enum=LinkBtn.chezmoi_guess)


class InputGuessSSH(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield Input(
            placeholder="Let chezmoi guess the SSH repo address",
            classes=Tcss.input_field,
        )
        yield FlatLink(ids=IDS.operate, link_enum=LinkBtn.chezmoi_guess)


class InitCollapsibles(VerticalGroup, AppType):
    def __init__(self) -> None:
        super().__init__()
        if self.app.splash_data is None:
            raise ValueError("self.app.splash_data is None in OperateScreen")
        self.splash_data = self.app.splash_data

    def compose(self) -> ComposeResult:
        yield Label("Operate Info", classes=Tcss.sub_section_label)
        yield CustomCollapsible(
            DoctorTable(ids=IDS.operate, doctor_data=self.splash_data.doctor),
            title="Doctor Output",
        )
        yield CustomCollapsible(
            PrettyTemplateData(self.splash_data.template_data),
            title="Template Data Output",
        )


class InputInitCloneRepo(HorizontalGroup):

    def __init__(self) -> None:
        super().__init__(id=IDS.operate.container.repo_input)

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


class InitScreen(OperateScreenBase):
    def __init__(self) -> None:
        super().__init__()
        self.guess_https: bool | None = None
        self.guess_ssh: bool | None = None
        self.init_cmd: WriteCmd
        self.repo_arg: str | None = None
        self.valid_url: bool = False

    def on_mount(self) -> None:
        super().on_mount()
        self.pre_op_container.mount(
            HorizontalGroup(
                Label(
                    SectionLabels.init_repo, classes=Tcss.main_section_label
                ),
                SwitchWithLabel(
                    ids=IDS.operate, switch_enum=Switches.init_repo_switch
                ),
            ),
            Static(id=IDS.operate.static.init_info),
            InputInitCloneRepo(),
            InitCollapsibles(),
        )
        self.query_exactly_one(SwitchWithLabel).add_class(Tcss.single_switch)
        self.repo_input = self.query_one(
            IDS.operate.container.repo_input_q, InputInitCloneRepo
        )
        self.repo_input.display = False
        self.init_info = self.query_one(IDS.operate.static.init_info_q, Static)
        self.exit_btn.label = OperateBtn.operate_exit.exit_app_label
        self.guess_docs_link = self.query_one(
            IDS.operate.link_button_id("#", btn=LinkBtn.chezmoi_guess),
            FlatLink,
        )
        self.guess_docs_link.display = False
        self.input_url = self.query_exactly_one(InputURL)
        self.input_ssh = self.query_exactly_one(InputSSH)
        self.input_guess_url = self.query_exactly_one(InputGuessURL)
        self.input_guess_ssh = self.query_exactly_one(InputGuessSSH)
        self.update_info_text()

    @on(Switch.Changed)
    def handle_switch_state(self, event: Switch.Changed) -> None:
        if event.value is True:
            self.op_btn.label = OperateBtn.init_repo.init_clone_label
            self.repo_input.display = True
            current_select = self.repo_input.query_exactly_one(
                Select[str]
            ).value
            # if current_select is not None:
            assert isinstance(current_select, str)
            self.update_info_text(select_value=current_select)
        else:
            self.op_btn.label = OperateBtn.init_repo.init_new_label
            self.repo_input.display = False
            self.update_info_text()

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
            return
        if self.op_btn.label == OperateBtn.init_repo.init_new_label:
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.init_new, changes_enabled=self.app.changes_enabled
            )
        elif (
            self.op_btn.label == OperateBtn.init_repo.init_clone_label
            and self.valid_url is True
        ):
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.init_guess_https,
                init_repo_arg=self.repo_arg,
                changes_enabled=self.app.changes_enabled,
            )
        else:
            self.notify(
                "Cannot perform init clone: unknown condition.",
                severity="error",
            )
            return

    @on(Select.Changed)
    def hanle_selection_change(self, event: Select.Changed) -> None:
        if not isinstance(event.value, str):
            return
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

        if self.repo_input.display is True:
            self.update_info_text(select_value=event.value)

    def update_info_text(self, select_value: str | None = None) -> None:
        if select_value is None:
            switch_state = self.query_exactly_one(Switch).value
            if switch_state is False:
                self.init_info.update(
                    "\n".join(
                        [
                            InitStaticText.init_new.value,
                            InitStaticText.init_switch_on.value,
                        ]
                    )
                )
            return
        if select_value == "https":
            info_text = "\n".join(
                [InitStaticText.https_url.value, InitStaticText.pat_info.value]
            )
        elif select_value == "ssh":
            info_text = InitStaticText.ssh_select.value
        elif select_value == "guess url":
            info_text = InitStaticText.guess_https.value
        elif select_value == "guess ssh":
            info_text = InitStaticText.guess_ssh.value
        else:
            raise ValueError("Invalid select_value in update_info_text")
        self.init_info.update(info_text)
