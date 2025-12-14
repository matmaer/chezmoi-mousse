from enum import StrEnum
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup
from textual.screen import Screen
from textual.validation import URL
from textual.widgets import Button, Footer, Input, Label, Select, Static

from chezmoi_mousse import (
    IDS,
    AppType,
    BindingAction,
    BindingDescription,
    Chars,
    LinkBtn,
    OperateBtn,
    SectionLabels,
    Tcss,
    WriteCmd,
)
from chezmoi_mousse.shared import (  # SwitchWithLabel,
    SSHSCP,
    ContentsView,
    CustomCollapsible,
    CustomHeader,
    DebugLog,
    DiffView,
    DoctorTable,
    FlatLink,
    InitCompletedMsg,
    OperateButtons,
    OperateLog,
    PrettyTemplateData,
)

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["ChezmoiInit", "OperateInfo", "OperateChezmoi"]


class InfoBorderSubtitle(StrEnum):
    add = f"local {Chars.right_arrow} chezmoi"
    apply = f"local {Chars.left_arrow} chezmoi"
    destroy = f"{Chars.x_mark} destroy {Chars.x_mark}"
    forget = f"{Chars.x_mark} forget {Chars.x_mark}"


class InfoLine(StrEnum):
    add_path = "[$text-primary]The path will be added to your chezmoi dotfile manager source state.[/]"
    apply_path = "[$text-primary]The path in the destination directory will be modified.[/]"
    auto_commit = f"[$text-warning]{Chars.warning_sign} Auto commit is enabled: files will also be committed.{Chars.warning_sign}[/]"
    autopush = f"[$text-warning]{Chars.warning_sign} Auto push is enabled: files will be pushed to the remote.{Chars.warning_sign}[/]"
    changes_disabled = "[dim]Changes are currently disabled, running commands with '--dry-run' flag.[/]"
    changes_enabled = f"[$text-warning]{Chars.warning_sign} Changes currently enabled, running commands without '--dry-run' flag.{Chars.warning_sign}[/]"
    destroy_path = "[$text-error]Permanently remove the path both from your home directory and chezmoi's source directory, make sure you have a backup![/]"
    diff_color = f"[$text-success]+ green lines will be added[/]\n[$text-error]- red lines will be removed[/]\n[dim]{Chars.bullet} dimmed lines for context[/]"
    forget_path = "[$text-primary]Remove the path from the source state, i.e. stop managing them.[/]"
    init_clone = "[$text-primary]Initialize a chezmoi from:[/]"
    init_new = "[$text-primary]Initialize a new chezmoi repository.[/]"
    re_add_path = (
        "[$text-primary]Overwrite the source state with current local path.[/]"
    )


class InitSubLabels(StrEnum):
    init_clone = "Optionally clone from an existing repository"
    operate_info = "Operate Info"


class InitStaticText(StrEnum):
    init_new = f"Click the [$primary-lighten-3 on $surface-lighten-1] {OperateBtn.init_repo.initial_label} [/] button to initialize a new chezmoi repository.\n"
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

    def on_mount(self) -> None:
        self.query_exactly_one(FlatLink).add_class(Tcss.guess_link)


class InputGuessSSH(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield Input(
            placeholder="Let chezmoi guess the SSH repo address",
            classes=Tcss.input_field,
        )
        yield FlatLink(ids=IDS.operate, link_enum=LinkBtn.chezmoi_guess)

    def on_mount(self) -> None:
        self.query_exactly_one(FlatLink).add_class(Tcss.guess_link)


class InitCollapsibles(VerticalGroup, AppType):
    def __init__(self) -> None:
        super().__init__()
        if self.app.splash_data is None:
            raise ValueError("self.app.splash_data is None in OperateScreen")
        self.splash_data = self.app.splash_data

    def compose(self) -> ComposeResult:
        yield CustomCollapsible(
            DoctorTable(ids=IDS.operate, doctor_data=self.splash_data.doctor),
            title="Doctor Output",
        )
        yield CustomCollapsible(
            PrettyTemplateData(self.splash_data.template_data),
            title="Template Data Output",
        )


class InputInitCloneRepo(HorizontalGroup):

    def compose(self) -> ComposeResult:
        yield Select[str].from_values(
            ["https", "ssh", "guess url", "guess ssh"],
            classes=Tcss.input_select,
            allow_blank=False,
            type_to_search=False,
        )
        yield InputURL()
        yield InputSSH()
        yield InputGuessURL()
        yield InputGuessSSH()


class OperateInfo(Static, AppType):

    git_autocommit: bool | None = None
    git_autopush: bool | None = None

    def __init__(self, ids: "AppIds") -> None:
        super().__init__()
        if self.app.operate_data is None:
            raise ValueError("self.app.operate_data is None in OperateInfo")
        self.op_data = self.app.operate_data
        self.btn_enum = self.op_data.btn_enum
        self.repo_arg: bool | None = None

    def on_mount(self) -> None:
        self.set_border_titles()
        self.write_info_lines()

    def set_border_titles(self) -> None:
        self.border_title = self.op_data.btn_label
        if self.btn_enum in (
            OperateBtn.add_file,
            OperateBtn.add_dir,
            OperateBtn.re_add_path,
        ):
            self.border_subtitle = InfoBorderSubtitle.add
        elif self.btn_enum == OperateBtn.apply_path:
            self.border_subtitle = InfoBorderSubtitle.apply
        elif self.btn_enum == OperateBtn.forget_path:
            self.border_subtitle = InfoBorderSubtitle.forget
        elif self.btn_enum == OperateBtn.destroy_path:
            self.border_subtitle = InfoBorderSubtitle.destroy

    def write_info_lines(self) -> None:
        self.update("")
        lines_to_write: list[str] = []
        if self.app.changes_enabled is True:
            lines_to_write.append(InfoLine.changes_enabled)
        else:
            lines_to_write.append(InfoLine.changes_disabled)

        if self.btn_enum in (OperateBtn.add_file, OperateBtn.add_dir):
            lines_to_write.append(InfoLine.add_path)
        elif self.btn_enum == OperateBtn.apply_path:
            lines_to_write.append(InfoLine.apply_path)
        elif self.btn_enum == OperateBtn.re_add_path:
            lines_to_write.append(InfoLine.re_add_path)
        elif self.btn_enum == OperateBtn.forget_path:
            lines_to_write.append(InfoLine.forget_path)
        elif self.btn_enum == OperateBtn.destroy_path:
            lines_to_write.append(InfoLine.destroy_path)
        elif self.btn_enum == OperateBtn.init_repo:
            if self.op_data.btn_label == OperateBtn.init_repo.init_clone_label:
                lines_to_write.append(
                    f"{InfoLine.init_clone} [$text-warning]{self.repo_arg}[/]"
                )
            else:
                lines_to_write.append(InfoLine.init_new)

        if self.btn_enum not in (OperateBtn.apply_path, OperateBtn.init_repo):
            if self.git_autocommit is True:
                lines_to_write.append(InfoLine.auto_commit)
            if self.git_autopush is True:
                lines_to_write.append(InfoLine.autopush)
        # show git diff color info
        if self.btn_enum in (OperateBtn.apply_path, OperateBtn.re_add_path):
            lines_to_write.append(InfoLine.diff_color)
        if self.op_data.node_data is not None:
            lines_to_write.append(
                f"[$text-primary]Operating on path: {self.op_data.node_data.path}[/]"
            )
        self.update("\n".join(lines_to_write))


class OperateScreenBase(Screen[None], AppType):
    def __init__(self) -> None:
        super().__init__()
        if self.app.operate_data is None:
            raise ValueError("self.app.operate_data is None in OperateScreen")
        self.op_data = self.app.operate_data

    def compose(self) -> ComposeResult:
        yield CustomHeader(IDS.operate)
        yield OperateInfo(IDS.operate)
        yield VerticalGroup(id=IDS.operate.container.pre_operate)
        with VerticalGroup(id=IDS.operate.container.post_operate):
            yield Label(
                SectionLabels.operate_output, classes=Tcss.main_section_label
            )
            yield OperateLog(ids=IDS.operate)
        if self.app.dev_mode:
            yield Label(SectionLabels.debug_log_output)
            yield DebugLog(IDS.operate)
        yield OperateButtons(
            ids=IDS.operate,
            buttons=(self.op_data.btn_enum, OperateBtn.operate_exit),
        )
        yield Footer(id=IDS.operate.footer)

    def on_mount(self) -> None:
        self.post_op_container = self.query_one(
            IDS.operate.container.post_operate_q, VerticalGroup
        )
        self.post_op_container.display = False
        self.pre_op_container = self.query_one(
            IDS.operate.container.pre_operate_q, VerticalGroup
        )
        self.op_btn = self.query_one(
            IDS.operate.operate_button_id("#", btn=self.op_data.btn_enum),
            Button,
        )
        self.op_btn.label = self.op_data.btn_label
        self.op_btn.tooltip = self.op_data.btn_tooltip
        self.exit_btn = self.query_one(
            IDS.operate.operate_button_id("#", btn=OperateBtn.operate_exit),
            Button,
        )

    def update_buttons(self) -> None:
        if (
            self.app.operate_cmd_result is None
            or self.app.operate_cmd_result.dry_run is True
        ):
            return
        self.op_btn.disabled = True
        self.op_btn.tooltip = None
        self.exit_btn.label = OperateBtn.operate_exit.reload_label

    def update_key_binding(self) -> None:
        if (
            self.app.operate_cmd_result is not None
            and self.app.operate_cmd_result.dry_run is True
        ):
            return
        new_description = BindingDescription.reload
        self.app.update_binding_description(
            BindingAction.exit_screen, new_description
        )

    def write_to_output_log(self) -> None:
        output_log = self.query_one(IDS.operate.logger.operate_q, OperateLog)
        if self.app.operate_cmd_result is not None:
            output_log.log_cmd_results(self.app.operate_cmd_result)


class ChezmoiInit(OperateScreenBase):
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
            Label(SectionLabels.init_repo, classes=Tcss.main_section_label),
            Static(InitStaticText.init_new),
            Label(InitSubLabels.init_clone, classes=Tcss.sub_section_label),
            Static(id=IDS.operate.static.init_info),
            InputInitCloneRepo(),
            Label(InitSubLabels.operate_info, classes=Tcss.sub_section_label),
            InitCollapsibles(),
        )
        self.init_info = self.query_one(IDS.operate.static.init_info_q, Static)
        self.init_info.update(
            "\n".join(
                [InitStaticText.https_url.value, InitStaticText.pat_info.value]
            )
        )
        self.guess_docs_link = self.query_one(
            IDS.operate.link_button_id("#", btn=LinkBtn.chezmoi_guess),
            FlatLink,
        )
        self.input_url = self.query_exactly_one(InputURL)
        self.input_ssh = self.query_exactly_one(InputSSH)
        self.input_guess_url = self.query_exactly_one(InputGuessURL)
        self.input_guess_ssh = self.query_exactly_one(InputGuessSSH)
        self.exit_btn.label = OperateBtn.operate_exit.exit_app_label

    @on(Select.Changed)
    def hanle_selection_change(self, event: Select.Changed) -> None:
        if event.value == "https":
            info_text = "\n".join(
                [InitStaticText.https_url.value, InitStaticText.pat_info.value]
            )
            self.guess_docs_link.display = False
            self.input_url.display = True
            self.input_ssh.display = False
            self.input_guess_url.display = False
            self.input_guess_ssh.display = False
        elif event.value == "ssh":
            info_text = InitStaticText.ssh_select.value
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
            info_text = InitStaticText.guess_https.value
        elif event.value == "guess ssh":
            self.input_url.display = False
            self.input_ssh.display = False
            self.input_guess_url.display = False
            self.input_guess_ssh.display = True
            info_text = InitStaticText.guess_ssh.value
            self.guess_docs_link.display = True
        else:
            info_text = ""
        init_info = self.query_one(IDS.operate.static.init_info_q, Static)
        init_info.update(info_text)

    def run_operate_command(self) -> None:
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
        elif event.button.label in (OperateBtn.operate_exit.reload_label,):
            self.app.post_message(InitCompletedMsg())
        elif event.button.label in (
            OperateBtn.operate_exit.close_label,
            OperateBtn.operate_exit.reload_label,
        ):
            self.dismiss()
        else:
            self.run_operate_command()


class OperateChezmoi(OperateScreenBase, AppType):

    def __init__(self) -> None:
        super().__init__()
        if self.app.operate_data is None:
            raise ValueError("self.app.operate_data is None in OperateScreen")
        self.reverse = (
            False if self.op_data.btn_enum == OperateBtn.apply_path else True
        )
        self.repo_arg: str | None = None

    def on_mount(self) -> None:
        super().on_mount()
        if self.op_data.btn_enum in (
            OperateBtn.apply_path,
            OperateBtn.re_add_path,
        ):
            self.pre_op_container.mount(
                DiffView(ids=IDS.operate, reverse=self.reverse)
            )
            diff_view = self.pre_op_container.query_one(
                IDS.operate.container.diff_q, DiffView
            )
            diff_view.node_data = self.op_data.node_data
            diff_view.remove_class(Tcss.border_title_top)
        else:
            self.pre_op_container.mount(ContentsView(ids=IDS.operate))
            contents_view = self.pre_op_container.query_one(
                IDS.operate.container.contents_q, ContentsView
            )
            contents_view.node_data = self.op_data.node_data
            contents_view.remove_class(Tcss.border_title_top)

    def run_operate_command(self) -> None:
        if self.op_data.node_data is not None:
            path_arg = self.op_data.node_data.path
        else:
            path_arg = None
        if self.op_data.btn_enum in (OperateBtn.add_file, OperateBtn.add_dir):
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.add,
                path_arg=path_arg,
                changes_enabled=self.app.changes_enabled,
            )
        elif self.op_data.btn_enum == OperateBtn.apply_path:
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.apply,
                path_arg=path_arg,
                changes_enabled=self.app.changes_enabled,
            )
        elif self.op_data.btn_enum == OperateBtn.re_add_path:
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.re_add,
                path_arg=path_arg,
                changes_enabled=self.app.changes_enabled,
            )
        elif self.op_data.btn_enum == OperateBtn.forget_path:
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.forget,
                path_arg=path_arg,
                changes_enabled=self.app.changes_enabled,
            )
        elif self.op_data.btn_enum == OperateBtn.destroy_path:
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.destroy,
                path_arg=path_arg,
                changes_enabled=self.app.changes_enabled,
            )
        if self.app.operate_cmd_result is None:
            raise ValueError(
                "self.app.operate_cmd_result is None after running command"
            )
        self.pre_op_container.display = False
        self.post_op_container.display = True
        self.write_to_output_log()
        if self.app.operate_cmd_result.dry_run is True:
            return
        self.update_buttons()
        self.update_key_binding()

    @on(Button.Pressed, Tcss.operate_button.dot_prefix)
    def handle_operate_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == OperateBtn.operate_exit.exit_app_label:
            self.app.exit()
        elif event.button.label in (OperateBtn.operate_exit.reload_label,):
            self.app.post_message(InitCompletedMsg())
        elif event.button.label == OperateBtn.operate_exit.cancel_label:
            self.app.operate_cmd_result = None
            self.dismiss()
        elif event.button.label in (
            OperateBtn.operate_exit.close_label,
            OperateBtn.operate_exit.reload_label,
        ):
            self.dismiss()
        else:
            self.run_operate_command()
