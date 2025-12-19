import re

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
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
    LinkBtn,
    OperateBtn,
    OperateStrings,
    SectionLabels,
    Switches,
    Tcss,
    WriteCmd,
)
from chezmoi_mousse.shared import (
    CurrentInitCmdMsg,
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
        self.https_arg: str | None = None
        self.ssh_arg: str | None = None
        self.guess_url_arg: str | None = None
        self.guess_ssh_arg: str | None = None
        self.https_cmd = WriteCmd.init_no_guess
        self.ssh_cmd = WriteCmd.init_no_guess
        self.guess_url_cmd = WriteCmd.init_guess_https
        self.guess_ssh_cmd = WriteCmd.init_guess_ssh

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
        self.post_current_init_cmd_msg()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        select_widget: Select[str] = self.query_exactly_one(Select[str])
        if select_widget.selection is None:
            return
        if select_widget.selection == "https":
            if (
                event.validation_result is not None
                and event.validation_result.is_valid
            ):
                self.notify("Valid URL entered, init clone enabled.")
                self.https_arg = event.value
                self.https_cmd = WriteCmd.init_no_guess
            else:
                self.notify("Invalid URL entered.", severity="error")
                self.https_arg = None
                self.https_cmd = None
        elif select_widget.selection == "ssh":
            if (
                event.validation_result is not None
                and event.validation_result.is_valid
            ):
                self.notify(
                    "Valid SSH SCP-style address entered, init clone enabled."
                )
                self.ssh_arg = event.value
                self.ssh_cmd = WriteCmd.init_no_guess
            else:
                self.notify(
                    "Invalid SSH SCP-style address entered.", severity="error"
                )
                self.ssh_arg = None
                self.ssh_cmd = None
        if select_widget.selection == "guess url":
            if (
                event.validation_result is not None
                and event.validation_result.is_valid
            ):
                self.notify(
                    "Ready to let chezmoi guess the https URL, init clone enabled."
                )
                self.guess_url_arg = event.value
                self.guess_url_cmd = WriteCmd.init_guess_https
            else:
                self.notify("Invalid URL entered.", severity="error")
                self.guess_url_arg = None
                self.guess_url_cmd = None
        elif select_widget.selection == "guess ssh":
            if (
                event.validation_result is not None
                and event.validation_result.is_valid
            ):
                self.notify(
                    "Ready to let chezmoi guess the ssh scp-style address, init clone enabled."
                )
                self.guess_ssh_arg = event.value
                self.guess_ssh_cmd = WriteCmd.init_guess_ssh
            else:
                self.notify(
                    "Invalid SSH SCP-style address entered.", severity="error"
                )
                self.guess_ssh_arg = None
                self.guess_ssh_cmd = None
        self.post_current_init_cmd_msg()

    def post_current_init_cmd_msg(self) -> None:
        self.app.post_message(
            CurrentInitCmdMsg(
                https_arg=self.https_arg,
                ssh_arg=self.ssh_arg,
                guess_url_arg=self.guess_url_arg,
                guess_ssh_arg=self.guess_ssh_arg,
                https_cmd=self.https_cmd,
                ssh_cmd=self.ssh_cmd,
                guess_url_cmd=self.guess_url_cmd,
                guess_ssh_cmd=self.guess_ssh_cmd,
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
        self.query_exactly_one(SwitchWithLabel).add_class(Tcss.single_switch)
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
        self.exit_btn.label = OperateBtn.operate_exit.exit_app_label
        self.repo_input = self.query_one(
            self.ids.container.repo_input_q, InputInitCloneRepo
        )
        self.repo_input.display = False
        self.init_static = self.query_one(self.ids.static.init_info_q, Static)
        self.update_operate_info()
        self.update_static_text()

    def update_operate_info(self) -> None:
        lines_to_write: list[str] = []
        if self.op_btn.label == OperateBtn.init_repo.init_new_label:
            lines_to_write.append(
                f"Run chezmoi {WriteCmd.init_new.pretty_cmd}"
            )
        if self.app.changes_enabled is True:
            lines_to_write.append(OperateStrings.changes_enabled)
        else:
            lines_to_write.append(OperateStrings.changes_disabled)
        self.operate_info.update("\n".join(lines_to_write))
        self.operate_info.border_title = self.operate_info.border_title = (
            self.op_data.btn_label
        )

    def update_static_text(self) -> None:
        switch_state = self.query_exactly_one(Switch).value
        if switch_state is False:
            self.init_static.update(OperateStrings.init_new_info)
            return
        current_select = self.repo_input.query_exactly_one(Select[str]).value
        if current_select == "https":
            self.init_static.update(OperateStrings.https_url)
        elif current_select == "ssh":
            self.init_static.update(OperateStrings.ssh_select)
        elif current_select == "guess url":
            self.init_static.update(OperateStrings.guess_https)
        elif current_select == "guess ssh":
            self.init_static.update(OperateStrings.guess_ssh)

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
        self.update_static_text()

    def action_exit_screen(self) -> None:
        if (
            self.app.operate_cmd_result is None
            or self.app.operate_cmd_result.dry_run is True
        ):
            self.app.exit()
        else:
            self.screen.dismiss()
