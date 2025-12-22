import re

from textual import on
from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup
from textual.screen import Screen
from textual.validation import URL, Failure, ValidationResult, Validator
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
    InitCloneData,
    LinkBtn,
    OpBtnLabels,
    OpBtnToolTips,
    OperateBtn,
    OperateStrings,
    SectionLabels,
    Switches,
    Tcss,
    WriteCmd,
)
from chezmoi_mousse.shared import (
    CustomCollapsible,
    CustomHeader,
    DebugLog,
    DoctorTable,
    FlatLink,
    InitCloneCmdMsg,
    OperateButtonMsg,
    OperateButtons,
    OperateLog,
    PrettyTemplateData,
    SwitchWithLabel,
)

__all__ = ["OperateInitScreen"]


class SSHSCP(Validator):
    """Validator that checks if a string is a valid SSH SCP-style address.

    SSH SCP-style addresses use the format `user@host:path` and are commonly used
    with Git and other SSH-based tools, however the format is not formally standardized.

    Examples of valid SSH SCP-style addresses:
        - `git@github.com:user/repo.git`
        - `user@example.com:path/to/repo.git`
        - `deploy@192.168.1.100:repos/myproject.git`
        - `git@gitlab.com:9999/group/project.git`

    Note:
        This validator is specifically for SCP-style syntax. For standard SSH URLs
        with explicit schemes (e.g., `ssh://user@host/path`), the standard `URL`
        validator from textual can be used.
    """

    # Pattern breakdown:
    # ^                           - Start of string
    # (?P<user>[a-zA-Z0-9._-]+)  - Username: alphanumeric, dots, hyphens, underscores
    # @                           - Literal @ separator
    # (?P<host>                   - Host group (domain or IPv4)
    #   (?:[a-zA-Z0-9-]+\.)*      - Subdomains (optional, repeating)
    #   [a-zA-Z0-9-]+             - Domain or last part of domain
    #   |                         - OR
    #   (?:\d{1,3}\.){3}\d{1,3}   - IPv4 address
    # )
    # :                           - Literal : separator
    # (?P<path>[^\s:]+)          - Path: any non-whitespace, non-colon characters
    # $                           - End of string
    SCP_PATTERN = re.compile(
        r"^(?P<user>[a-zA-Z0-9._-]+)"
        r"@"
        r"(?P<host>(?:[a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+|(?:\d{1,3}\.){3}\d{1,3})"
        r":"
        r"(?P<path>[^\s:]+)$"
    )

    class InvalidSSHSCP(Failure):
        """Indicates that the SSH SCP-style address is not valid."""

    def validate(self, value: str) -> ValidationResult:
        """Validates that `value` is a valid SSH SCP-style address.

        Args:
            value: The value to validate.

        Returns:
            The result of the validation.
        """
        if not value:
            return ValidationResult.failure(
                [SSHSCP.InvalidSSHSCP(self, value)]
            )

        if not self.SCP_PATTERN.match(value):
            return ValidationResult.failure(
                [SSHSCP.InvalidSSHSCP(self, value)]
            )

        return self.success()

    def describe_failure(self, failure: Failure) -> str | None:
        """Describes why the validator failed.

        Args:
            failure: Information about why the validation failed.

        Returns:
            A string description of the failure.
        """
        if isinstance(failure, SSHSCP.InvalidSSHSCP):
            return "Must be a valid SSH SCP-style address."
        return None


class GUESS_HTTPS(Validator):
    """Lenient validator for chezmoi HTTPS guess inputs.

    Validates inputs that will be guessed as HTTPS URLs by chezmoi.
    This is intentionally permissive since chezmoi will handle the actual
    guessing and transformation logic. If the input doesn't match any known
    pattern, chezmoi will pass it through unchanged and report an error
    during the clone operation.

    Accepts HTTPS-style formats:
        - Shorthand paths without @ symbols (chezmoi expands to HTTPS)
        - Optional https:// scheme prefix
        - Tildes (for SourceHut ~user format)

    Examples:
        - `user/repo` → `https://github.com/user/repo.git`
        - `github.com/user/repo` → `https://github.com/user/repo.git`
        - `gitlab.com/org/project` → `https://gitlab.com/org/project.git`
        - `sr.ht/~user/dotfiles` → `https://git.sr.ht/~user/dotfiles`
        - `https://example.com/user/repo` → `https://example.com/user/repo.git`
    """

    # Pattern breakdown:
    # ^                    - Start of string
    # (?:https?://)?       - Optional http:// or https:// scheme (non-capturing group)
    # [                    - Character class start
    #   a-zA-Z             - Letters (uppercase and lowercase)
    #   0-9                - Digits
    #   .                  - Dots (for domains like github.com)
    #   _                  - Underscores (for usernames/repos)
    #   /                  - Forward slashes (for paths)
    #   :                  - Colons (for schemes or ports)
    #   \-                 - Hyphens (escaped in character class)
    #   ~                  - Tildes (for SourceHut ~user format)
    # ]+                   - One or more of the above characters
    # $                    - End of string
    # Note: Excludes @ symbol as it indicates SSH-style format
    VALID_PATTERN = re.compile(r"^(?:https?://)?[a-zA-Z0-9._/:\-~]+$")

    class InvalidGuessHTTPS(Failure):
        """Indicates that the HTTPS guess input contains invalid characters."""

    def validate(self, value: str) -> ValidationResult:
        """Validates that `value` is suitable for HTTPS guessing.

        Args:
            value: The value to validate.

        Returns:
            The result of the validation.
        """
        if not value:
            return ValidationResult.failure(
                [GUESS_HTTPS.InvalidGuessHTTPS(self, value)]
            )

        if not self.VALID_PATTERN.match(value):
            return ValidationResult.failure(
                [GUESS_HTTPS.InvalidGuessHTTPS(self, value)]
            )

        return self.success()

    def describe_failure(self, failure: Failure) -> str | None:
        """Describes why the validator failed.

        Args:
            failure: Information about why the validation failed.

        Returns:
            A string description of the failure.
        """
        if isinstance(failure, GUESS_HTTPS.InvalidGuessHTTPS):
            return "Must be valid for HTTPS guessing (a-z, 0-9, . / : - ~, optional https://)"
        return None


class GUESS_SSH(Validator):
    """Lenient validator for chezmoi SSH guess inputs.

    Validates inputs that will be guessed as SSH addresses by chezmoi.
    This is intentionally permissive since chezmoi will handle the actual
    guessing and transformation logic. If the input doesn't match any known
    pattern, chezmoi will pass it through unchanged and report an error
    during the clone operation.

    Accepts SSH-style formats:
        - Shorthand paths (chezmoi expands to SSH SCP-style)
        - Optional @ symbols for explicit user@host format
        - Tildes (for SourceHut ~user format)

    Examples:
        - `user/repo` → `git@github.com:user/repo.git`
        - `github.com/user/repo` → `git@github.com:user/repo.git`
        - `gitlab.com/org/project` → `git@gitlab.com:org/project.git`
        - `sr.ht/~user/dotfiles` → `git@git.sr.ht:~user/dotfiles`
        - `git@github.com:user/repo.git` → `git@github.com:user/repo.git`
    """

    # Pattern breakdown:
    # ^                - Start of string
    # [                - Character class start
    #   a-zA-Z         - Letters (uppercase and lowercase)
    #   0-9            - Digits
    #   .              - Dots (for domains like github.com)
    #   _              - Underscores (for usernames)
    #   /              - Forward slashes (for paths)
    #   :              - Colons (for SCP-style user@host:path format)
    #   \-             - Hyphens (escaped in character class)
    #   ~              - Tildes (for SourceHut ~user format)
    #   @              - At symbols (for user@host format)
    # ]+               - One or more of the above characters
    # $                - End of string
    VALID_PATTERN = re.compile(r"^[a-zA-Z0-9._/:\-~@]+$")

    class InvalidGuessSSH(Failure):
        """Indicates that the SSH guess input contains invalid characters."""

    def validate(self, value: str) -> ValidationResult:
        """Validates that `value` is suitable for SSH guessing.

        Args:
            value: The value to validate.

        Returns:
            The result of the validation.
        """
        if not value:
            return ValidationResult.failure(
                [GUESS_SSH.InvalidGuessSSH(self, value)]
            )

        if not self.VALID_PATTERN.match(value):
            return ValidationResult.failure(
                [GUESS_SSH.InvalidGuessSSH(self, value)]
            )

        return self.success()

    def describe_failure(self, failure: Failure) -> str | None:
        """Describes why the validator failed.

        Args:
            failure: Information about why the validation failed.

        Returns:
            A string description of the failure.
        """
        if isinstance(failure, GUESS_SSH.InvalidGuessSSH):
            return "Must be valid for SSH guessing (a-z, 0-9, . / : - ~ @)"
        return None


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
            validate_on=["submitted"],
            validators=GUESS_HTTPS(),
            classes=Tcss.input_field,
        )
        yield FlatLink(ids=IDS_OPERATE_INIT, link_enum=LinkBtn.chezmoi_guess)


class InputGuessSSH(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield Input(
            placeholder="Let chezmoi guess the SSH repo address",
            validate_on=["submitted"],
            validators=GUESS_SSH(),
            classes=Tcss.input_field,
        )
        yield FlatLink(ids=IDS_OPERATE_INIT, link_enum=LinkBtn.chezmoi_guess)


class InputInitCloneRepo(HorizontalGroup, AppType):

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
            allow_blank=False,
            classes=Tcss.input_select,
            type_to_search=False,
            value="https",
        )
        yield InputURL()
        yield InputSSH()
        yield InputGuessURL()
        yield InputGuessSSH()

    def on_mount(self) -> None:
        self.input_url = self.query_exactly_one(InputURL)
        self.input_ssh = self.query_exactly_one(InputSSH)
        self.input_guess_url = self.query_exactly_one(InputGuessURL)
        self.input_guess_ssh = self.query_exactly_one(InputGuessSSH)
        self.input_ssh.display = False
        self.input_guess_url.display = False
        self.input_guess_ssh.display = False
        self.init_repo_data: InitCloneData | None = None

    def on_select_changed(self, event: Select.Changed) -> None:
        self.input_url.display = False
        self.input_ssh.display = False
        self.input_guess_url.display = False
        self.input_guess_ssh.display = False

        if event.value == "https":
            self.input_url.display = True
        elif event.value == "ssh":
            self.input_ssh.display = True
        elif event.value == "guess url":
            self.input_guess_url.display = True
        elif event.value == "guess ssh":
            self.input_guess_ssh.display = True

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.validation_result is None:
            self.notify(
                "No validation result available on input submitted.",
                severity="error",
            )
            return
        select_widget: Select[str] = self.query_exactly_one(Select[str])
        if select_widget.selection is None:
            return
        init_cmd = None
        init_arg = event.value
        valid_arg = None
        if select_widget.selection == "https":
            init_cmd = WriteCmd.init_no_guess
            if event.validation_result.is_valid:
                self.notify("Valid URL entered.")
                valid_arg = True
            else:
                self.notify("Invalid URL entered.", severity="error")
                valid_arg = False
        elif select_widget.selection == "ssh":
            init_cmd = WriteCmd.init_no_guess
            if event.validation_result.is_valid:
                self.notify("Valid SSH SCP-style address entered.")
                valid_arg = True
            else:
                self.notify(
                    "Invalid SSH SCP-style address entered.", severity="error"
                )
                valid_arg = False
        elif select_widget.selection == "guess url":
            init_cmd = WriteCmd.init_guess_https
            if event.validation_result.is_valid:
                self.notify("Valid input for chezmoi to guess the https URL.")
                valid_arg = True
            else:
                self.notify(
                    "Invalid guess input entered for https.", severity="error"
                )
                valid_arg = False
        elif select_widget.selection == "guess ssh":
            init_cmd = WriteCmd.init_guess_ssh
            if event.validation_result.is_valid:
                self.notify(
                    "Valid input for chezmoi to guess the ssh address."
                )
                valid_arg = True
            else:
                self.notify(
                    "Invalid SSH SCP-style address entered.", severity="error"
                )
        if init_cmd is None or valid_arg is None:
            raise ValueError("Failed to determine init clone command data.")
        self.screen.post_message(
            InitCloneCmdMsg(
                InitCloneData(
                    init_cmd=init_cmd, init_arg=init_arg, valid_arg=valid_arg
                )
            )
        )


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


class OperateInitScreen(Screen[None], AppType):

    def __init__(self) -> None:
        super().__init__()
        self.ids = IDS_OPERATE_INIT
        self.init_clone_data: InitCloneData | None = None
        self.valid_arg: bool = False
        self.init_arg: str | None = None
        self.init_cmd = WriteCmd.init_new

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
        yield OperateButtons(ids=self.ids)
        yield Footer(id=self.ids.footer)

    def on_mount(self) -> None:
        self.query_exactly_one(SwitchWithLabel).add_class(Tcss.single_switch)
        self.operate_buttons = self.query_one(
            self.ids.container.operate_buttons_q, OperateButtons
        )
        self.app.update_binding_description(
            BindingAction.exit_screen, BindingDescription.reload
        )
        self.post_op_container = self.query_one(
            self.ids.container.post_operate_q, VerticalGroup
        )
        self.post_op_container.display = False
        self.init_info = self.query_one(self.ids.static.init_info_q, Static)
        self.operate_info = self.query_one(
            self.ids.static.operate_info_q, Static
        )
        self.operate_info.border_title = OpBtnLabels.init_new
        self.init_new_btn = self.query_one(
            self.ids.operate_btn.init_new_q, Button
        )
        self.init_new_btn.display = True
        self.init_new_btn.disabled = False
        self.init_clone_btn = self.query_one(
            self.ids.operate_btn.init_clone_q, Button
        )
        self.init_clone_btn.display = True
        self.init_clone_btn.disabled = True
        self.exit_btn = self.query_one(
            self.ids.operate_btn.operate_exit_q, Button
        )
        self.exit_btn.display = True
        self.exit_btn.label = OpBtnLabels.exit_app
        self.repo_input = self.query_one(
            self.ids.container.repo_input_q, InputInitCloneRepo
        )
        self.repo_input.display = False
        self.update_operate_info()
        self.update_init_info()

    def update_operate_info(self) -> None:
        self.operate_info.border_title = self.init_new_btn.label
        lines_to_write: list[str] = []
        if self.app.changes_enabled is True:
            lines_to_write.append(OperateStrings.changes_enabled)
        else:
            lines_to_write.append(OperateStrings.changes_disabled)
        if self.query_exactly_one(Switch).value is False:
            lines_to_write.append(
                "Ready to run [$text-success] chezmoi "
                f"{WriteCmd.init_new.pretty_cmd}[/]"
            )
            self.operate_info.update("\n".join(lines_to_write))
            return
        if self.init_clone_data is None:
            lines_to_write.append(
                "[$text-error]No init clone input provided yet."
            )
            self.init_clone_btn.disabled = True
        if (
            self.init_clone_data is not None
            and self.init_clone_data.init_cmd == WriteCmd.init_no_guess
        ):
            if self.init_clone_data.valid_arg is True:
                lines_to_write.append(
                    (
                        '[$text-success]Ready to run "chezmoi '
                        f"{WriteCmd.init_no_guess.pretty_cmd} "
                        f'{self.init_clone_data.init_arg}"[/]'
                    )
                )
            elif self.init_clone_data.valid_arg is False:
                lines_to_write.append(
                    f"[$text-error]{WriteCmd.init_no_guess.pretty_cmd} "
                    ": invalid URL or SSH SCP-style address."
                )
        elif (
            self.init_clone_data is not None
            and self.init_clone_data.init_cmd == WriteCmd.init_guess_https
        ):
            if self.init_clone_data.valid_arg is True:
                lines_to_write.append(
                    (
                        '[$text-success]Ready to run "chezmoi '
                        f"{self.init_clone_data.init_cmd.pretty_cmd} "
                        f"{self.init_clone_data.init_arg}[/]"
                    )
                )
            elif self.init_clone_data.valid_arg is False:
                lines_to_write.append(
                    f"[$text-error]{self.init_clone_data.init_cmd.pretty_cmd} "
                    ": invalid guess https input."
                )
        elif (
            self.init_clone_data is not None
            and self.init_clone_data.init_cmd == WriteCmd.init_guess_ssh
        ):
            if self.init_clone_data.valid_arg is True:
                lines_to_write.append(
                    (
                        '[$text-success]Ready to run "chezmoi '
                        f"{self.init_clone_data.init_cmd.pretty_cmd} "
                        f"{self.init_clone_data.init_arg}[/]"
                    )
                )
            elif self.init_clone_data.valid_arg is False:
                lines_to_write.append(
                    f"[$text-error]{self.init_clone_data.init_cmd.pretty_cmd} "
                    ": invalid guess ssh input."
                )
        self.operate_info.update("\n".join(lines_to_write))

    def update_init_info(self) -> None:
        if self.query_exactly_one(Switch).value is False:
            self.init_info.update(OperateStrings.init_new_info)
            return
        current_select = self.repo_input.query_exactly_one(Select[str]).value
        if current_select == "https":
            self.init_info.update(OperateStrings.https_url)
        elif current_select == "ssh":
            self.init_info.update(OperateStrings.ssh_select)
        elif current_select == "guess url":
            self.init_info.update(OperateStrings.guess_https)
        elif current_select == "guess ssh":
            self.init_info.update(OperateStrings.guess_ssh)

    def run_operate_command(self) -> None:
        self.app.init_cmd_result = self.app.chezmoi.perform(
            write_cmd=self.init_cmd,
            init_arg=self.init_arg,
            changes_enabled=self.app.changes_enabled,
        )
        self.pre_op_container = self.query_one(
            self.ids.container.pre_operate_q, VerticalGroup
        )
        self.pre_op_container.display = False
        self.post_op_container.display = True
        output_log = self.query_one(self.ids.logger.operate_q, OperateLog)
        output_log.log_cmd_results(self.app.init_cmd_result)
        if (
            self.app.changes_enabled is True
            and self.app.init_cmd_result.exit_code == 0
        ):
            self.app.init_needed = False
            self.init_new_btn.disabled = True
            self.init_new_btn.tooltip = None
            self.init_clone_btn.disabled = True
            self.init_clone_btn.tooltip = None
            self.exit_btn.label = OpBtnLabels.reload

    @on(Switch.Changed)
    def handle_switch_state(self, event: Switch.Changed) -> None:
        if event.value is True:
            self.repo_input.display = True
            self.init_new_btn.disabled = True
            self.init_new_btn.tooltip = OpBtnToolTips.init_new_disabled
            if self.valid_arg is True:
                self.init_clone_btn.disabled = False
                self.init_clone_btn.tooltip = None
            elif self.valid_arg is False:
                self.init_clone_btn.disabled = True
                self.init_clone_btn.tooltip = OpBtnToolTips.init_clone_disabled
        elif event.value is False:
            self.repo_input.display = False
            self.init_new_btn.disabled = False
            self.init_clone_btn.disabled = True
            self.init_clone_btn.tooltip = OpBtnToolTips.init_clone_switch_off
        self.update_init_info()
        self.update_operate_info()

    @on(OperateButtonMsg)
    def handle_operate_button_pressed(self, msg: OperateButtonMsg) -> None:
        if msg.btn_enum == OperateBtn.init_new:
            self.init_cmd = WriteCmd.init_new
            self.init_arg = None
        else:
            self.notify("Init clone not yet implemented.")
        self.run_operate_command()

    @on(InitCloneCmdMsg)
    def handle_init_clone_cmd_msg(self, msg: InitCloneCmdMsg) -> None:
        self.init_clone_data = msg.init_clone_data
        if self.init_clone_data.valid_arg is False:
            self.init_clone_btn.disabled = True
        else:
            self.init_clone_btn.disabled = False
        self.update_operate_info()

    @on(Select.Changed)
    def hanle_selection_change(self, event: Select.Changed) -> None:
        self.update_operate_info()
