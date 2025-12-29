"""This module does not import anything from textual, it only contains classes
imported at module init before launching the textual app, and attributes
accessed after the app is launched.

The initial_label attribute is used to construct the OpButton class in
shared/_buttons.py.
"""

from dataclasses import dataclass
from enum import Enum, StrEnum

from ._chezmoi_command import WriteCmd

__all__ = ["OpBtnLabels", "OpBtnEnum"]


# class OperateStrings(StrEnum):
#     add_subtitle = f"path on disk {Chars.right_arrow} chezmoi repo"
#     apply_subtitle = f"chezmoi repo {Chars.right_arrow} path on disk"
#     auto_commit = (
#         f"[$text-warning]{Chars.warning_sign} Auto commit is enabled: "
#         "files will also be committed."
#         f"{Chars.warning_sign}[/]"
#     )
#     auto_push = (
#         f"[$text-warning]{Chars.warning_sign} Auto push is enabled: "
#         "files will be pushed to the remote."
#         f"{Chars.warning_sign}[/]"
#     )
#     cmd_output_subtitle = "Command Output"
#     destroy_path = (
#         "[$text-error]Permanently remove the path from disk and "
#         " chezmoi. MAKE SURE YOU HAVE A BACKUP![/]"
#     )
#     destroy_subtitle = (
#         f"{Chars.x_mark} delete on disk and in chezmoi repo {Chars.x_mark}"
#     )
#     error_subtitle = "Operation failed with errors"
#     forget_path = (
#         "[$text-primary]Remove the path from the source state, i.e. stop "
#         "managing them.[/]"
#     )
#     forget_subtitle = (
#         f"{Chars.x_mark} leave on disk but remove from chezmoi repo "
#         f"{Chars.x_mark}"
#     )
#     guess_https = "Let chezmoi guess the best URL to clone from."
#     guess_ssh = (
#         "Let chezmoi guess the best ssh scp-style address to clone from."
#     )
#     https_url = (
#         "Enter a complete URL, e.g., "
#         "[$text-primary]https://github.com/user/repo.git[/]. "
#         "If you have a PAT, make sure to include it in the URL, for example: "
#         "[$text-primary]https://username:ghp_123456789abcdef@github.com/"
#         "username/my-dotfiles.git[/] and delete the PAT after use."
#     )
#     init_new_info = (
#         "Ready to initialize a new chezmoi repository. Toggle the "
#         "[$foreground-darken-1 on $surface-lighten-1] "
#         f"{Switches.init_repo_switch.label} [/]"
#         "switch to initialize by cloning an existing Github repository."
#     )
#     read_file = "[$success]Path.read()[/]"
#     ready_to_run = "[$success]Ready to run: [/]"
#     re_add_subtitle = (
#         f"path on disk {Chars.right_arrow} overwrite chezmoi repo"
#     )
#     ssh_select = (
#         "Enter an SSH SCP-style URL, e.g., "
#         "[$text_primary]git@github.com:user/repo.git[/]. If the repository is"
#         "private, make sure you have your SSH key pair set up before using "
#         "this option."
#     )
#     success_subtitle = "Operation completed successfully"


class OpBtnLabels(StrEnum):
    add_run = "Run Chezmoi Add"
    add_review = "Review Add Path"
    apply_review = "Review Apply Path"
    apply_run = "Run Chezmoi Apply"
    cancel = "Cancel"
    destroy_run = "Run Chezmoi Destroy"
    destroy_review = "Review Destroy Path"
    exit_app = "Exit App"
    forget_run = "Run Chezmoi Forget"
    forget_review = "Review Forget Path"
    init_run = "Run Chezmoi Init"
    init_review = "Review Init Chezmoi"
    re_add_review = "Review Re-Add Path"
    re_add_run = "Run Chezmoi Re-Add"
    reload = "Reload"


@dataclass(slots=True)
class OpBtnData:
    label: str
    write_cmd: WriteCmd


class OpBtnEnum(Enum):
    add = OpBtnData(label=OpBtnLabels.add_review, write_cmd=WriteCmd.add)
    apply = OpBtnData(label=OpBtnLabels.apply_review, write_cmd=WriteCmd.apply)
    destroy = OpBtnData(
        label=OpBtnLabels.destroy_review, write_cmd=WriteCmd.destroy
    )
    forget = OpBtnData(
        label=OpBtnLabels.forget_review, write_cmd=WriteCmd.forget
    )
    re_add = OpBtnData(
        write_cmd=WriteCmd.re_add, label=OpBtnLabels.re_add_review
    )
    init = OpBtnData(
        label=OpBtnLabels.init_review, write_cmd=WriteCmd.init_new
    )

    # Allow access to dataclass attributes directly from the Enum member,
    # without needing to go through the value attribute

    @property
    def label(self) -> str:
        return self.value.label

    @property
    def write_cmd(self) -> WriteCmd:
        return self.value.write_cmd
