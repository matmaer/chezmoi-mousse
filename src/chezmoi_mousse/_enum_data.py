from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import TYPE_CHECKING

from ._run_cmd import Chars, WriteCmd
from ._str_enums import SwitchLabel

if TYPE_CHECKING:
    from pathlib import Path

__all__ = ["OpBtnEnum", "OpBtnLabel", "OpInfoString", "SwitchEnum"]


class OpInfoString(StrEnum):
    add_path_info = (
        "[dim]Add new targets to the source state. If adding a directory, it"
        " will be recursed in.[/]"
    )
    add_subtitle = f"local path {Chars.right_arrow} chezmoi repo"
    apply_path_info = (
        "[dim]Chezmoi will ensure that the path is in the target state. "
        "The command will run without prompting. "
        "For targets modified since chezmoi last wrote it. If adding a "
        "directory, it will be recursed in.[/]"
    )
    apply_subtitle = f"chezmoi repo {Chars.right_arrow} path on disk"
    command_completed = "Command completed"
    destroy_path_info = (
        "[$text-error]Permanently remove the path from disk and chezmoi. MAKE "
        "SURE YOU HAVE A BACKUP![/]"
    )
    destroy_subtitle = (
        f"[$text-error]{Chars.x_mark}[/] delete on disk and in chezmoi repo "
        f"[$text-error]{Chars.x_mark}[/]"
    )
    forget_path_info = "[dim]Remove from the source state, i.e. stop managing them.[/]"
    forget_subtitle = f"leave on disk {Chars.right_arrow} chezmoi repo {Chars.x_mark}"
    ready_to_run = "[$text]Ready to run[/]"
    run_completed = "[$text]Command completed[/]"
    re_add_path_info = (
        "[dim]Re-add modified files in the target state, preserving "
        "any encrypted_ attributes. chezmoi will not overwrite templates, and "
        "all entries that are not files are ignored. If adding a directory, it"
        " will be recursed in.[/]"
    )
    re_add_subtitle = f"path on disk {Chars.right_arrow} overwrite chezmoi repo"
    init_new_info = (
        "Ready to initialize a new chezmoi repository. Toggle the "
        "[$foreground-darken-1 on $surface-lighten-1] "
        f"{SwitchLabel.init_repo} [/]"
        "switch to initialize by cloning an existing Github repository."
    )
    init_subtitle = "initialize chezmoi repository"


class OpBtnLabel(StrEnum):
    add_review = "Review Add Path"
    add_run = "Run Chezmoi Add"
    apply_review = "Review Apply Path"
    apply_run = "Run Chezmoi Apply"
    cancel = "Cancel"
    create_diffs = "Create Diffs"
    create_paths = "Create Test Paths"
    destroy_review = "Review Destroy Path"
    destroy_run = "Run Chezmoi Destroy"
    exit_app = "Exit App"
    forget_review = "Review Forget Path"
    forget_run = "Run Chezmoi Forget"
    init_review = "Review Chezmoi Init"
    init_run = "Run Chezmoi Init"
    list_test_paths = "List Test Paths"
    log_memory = "Log Memory Usage"
    re_add_review = "Review Re-Add Path"
    re_add_run = "Run Chezmoi Re-Add"
    refresh_tree = "Refresh Trees"
    reload = "Reload"
    remove_paths = "Remove Test Paths"

    @property
    def normalized_label(self) -> str:
        return self.value.translate(
            str.maketrans({" ": "_", "-": "_", "(": "", ")": ""})
        ).lower()


@dataclass(slots=True)
class OpBtnData:
    label: str
    write_cmd: WriteCmd | None = None
    op_info_string: str | None = None
    op_info_title: str | None = None
    op_info_subtitle: str | None = None
    path_arg: "Path | None" = None


class OpBtnEnum(Enum):

    cancel = OpBtnData(label=OpBtnLabel.cancel)
    create_diffs = OpBtnData(label=OpBtnLabel.create_diffs)
    create_paths = OpBtnData(label=OpBtnLabel.create_paths)
    exit_app = OpBtnData(label=OpBtnLabel.exit_app)
    list_test_paths = OpBtnData(label=OpBtnLabel.list_test_paths)
    log_memory = OpBtnData(label=OpBtnLabel.log_memory)
    refresh_tree = OpBtnData(label=OpBtnLabel.refresh_tree)
    reload = OpBtnData(label=OpBtnLabel.reload)
    remove_paths = OpBtnData(label=OpBtnLabel.remove_paths)

    add_review = OpBtnData(
        label=OpBtnLabel.add_review,
        write_cmd=WriteCmd.add,
        op_info_string=OpInfoString.add_path_info,
        op_info_subtitle=OpInfoString.add_subtitle,
        op_info_title=OpInfoString.ready_to_run,
    )
    add_run = OpBtnData(
        label=OpBtnLabel.add_run,
        write_cmd=WriteCmd.add,
        op_info_string=OpInfoString.add_path_info,
        op_info_title=OpInfoString.run_completed,
    )
    apply_review = OpBtnData(
        label=OpBtnLabel.apply_review,
        write_cmd=WriteCmd.apply,
        op_info_string=OpInfoString.apply_path_info,
        op_info_subtitle=OpInfoString.apply_subtitle,
        op_info_title=OpInfoString.ready_to_run,
    )
    apply_run = OpBtnData(
        label=OpBtnLabel.apply_run,
        write_cmd=WriteCmd.apply,
        op_info_string=OpInfoString.apply_path_info,
        op_info_title=OpInfoString.run_completed,
    )
    destroy_review = OpBtnData(
        label=OpBtnLabel.destroy_review,
        write_cmd=WriteCmd.destroy,
        op_info_string=OpInfoString.destroy_path_info,
        op_info_subtitle=OpInfoString.destroy_subtitle,
        op_info_title=OpInfoString.ready_to_run,
    )
    destroy_run = OpBtnData(
        label=OpBtnLabel.destroy_run,
        write_cmd=WriteCmd.destroy,
        op_info_string=OpInfoString.destroy_path_info,
        op_info_title=OpInfoString.run_completed,
    )
    forget_review = OpBtnData(
        label=OpBtnLabel.forget_review,
        write_cmd=WriteCmd.forget,
        op_info_string=OpInfoString.forget_path_info,
        op_info_subtitle=OpInfoString.forget_subtitle,
        op_info_title=OpInfoString.ready_to_run,
        path_arg=None,
    )
    forget_run = OpBtnData(
        label=OpBtnLabel.forget_run,
        write_cmd=WriteCmd.forget,
        op_info_string=OpInfoString.forget_path_info,
        op_info_title=OpInfoString.run_completed,
    )
    re_add_review = OpBtnData(
        label=OpBtnLabel.re_add_review,
        write_cmd=WriteCmd.re_add,
        op_info_string=OpInfoString.re_add_path_info,
        op_info_subtitle=OpInfoString.re_add_subtitle,
        op_info_title=OpInfoString.ready_to_run,
    )
    re_add_run = OpBtnData(
        label=OpBtnLabel.re_add_run,
        write_cmd=WriteCmd.re_add,
        op_info_string=OpInfoString.re_add_path_info,
        op_info_title=OpInfoString.run_completed,
    )
    init_review = OpBtnData(
        label=OpBtnLabel.init_review,
        write_cmd=WriteCmd.init_new,
        op_info_string=OpInfoString.init_new_info,
        op_info_subtitle=OpInfoString.init_subtitle,
        op_info_title=OpInfoString.ready_to_run,
    )
    init_run = OpBtnData(
        label=OpBtnLabel.init_run,
        write_cmd=WriteCmd.init_new,
        op_info_string=OpInfoString.init_new_info,
        op_info_title=OpInfoString.run_completed,
    )

    # Allow access to dataclass attributes directly from the Enum member,
    # without needing to go through the value attribute

    @property
    def label(self) -> str:
        return self.value.label

    @property
    def write_cmd(self) -> WriteCmd:
        if self.value.write_cmd is None:
            raise ValueError(f"OpBtnEnum member {self.name} has no write_cmd")
        return self.value.write_cmd

    @property
    def op_info_string(self) -> str:
        if self.value.op_info_string is None:
            raise ValueError(f"OpBtnEnum member {self.name} has no op_info_string")
        return self.value.op_info_string

    @property
    def op_info_subtitle(self) -> str | None:
        return self.value.op_info_subtitle

    @property
    def op_info_title(self) -> str | None:
        return self.value.op_info_title

    @property
    def path_arg(self) -> "Path | None":
        return self.value.path_arg

    @path_arg.setter
    def path_arg(self, value: "Path | None") -> None:
        self.value.path_arg = value

    @classmethod
    def review_to_run(cls, btn_label: OpBtnLabel) -> "OpBtnEnum":
        _mapping = {
            OpBtnLabel.add_review: cls.add_run,
            OpBtnLabel.apply_review: cls.apply_run,
            OpBtnLabel.destroy_review: cls.destroy_run,
            OpBtnLabel.forget_review: cls.forget_run,
            OpBtnLabel.re_add_review: cls.re_add_run,
        }
        return _mapping[btn_label]

    @classmethod
    def review_btn_enums(cls) -> set["OpBtnEnum"]:
        return {
            cls.add_review,
            cls.apply_review,
            cls.destroy_review,
            cls.forget_review,
            cls.re_add_review,
        }

    @classmethod
    def run_btn_enums(cls) -> set["OpBtnEnum"]:
        return {
            cls.add_run,
            cls.apply_run,
            cls.destroy_run,
            cls.forget_run,
            cls.re_add_run,
        }


@dataclass(frozen=True, slots=True)
class SwitchData:
    label: str
    enabled_tooltip: str


class SwitchEnum(Enum):

    init_repo_switch = SwitchData(
        label=SwitchLabel.init_repo,
        enabled_tooltip=(
            "Initialize a new chezmoi repository, or clone an existing remote "
            "chezmoi repository."
        ),
    )
    expand_all = SwitchData(
        label=SwitchLabel.expand_all,
        enabled_tooltip=(
            "Expand all managed directories. Showing unchanged depending on the "
            '"show unchanged files" switch.'
        ),
    )
    unchanged = SwitchData(
        label=SwitchLabel.unchanged,
        enabled_tooltip=(
            "Include unchanged paths which are not found in the "
            "'chezmoi status' output."
        ),
    )
    managed_dirs = SwitchData(
        label=SwitchLabel.managed_dirs,
        enabled_tooltip=("If enabled, only already managed directories are shown."),
    )
    unwanted = SwitchData(
        label=SwitchLabel.unwanted,
        enabled_tooltip=(
            "Include files and directories considered as 'unwanted' for a dotfile "
            "manager. These include cache, temporary, trash (recycle bin) and other "
            "similar files or directories."
        ),
    )

    @property
    def label(self) -> str:
        return self.value.label

    @property
    def enabled_tooltip(self) -> str:
        return self.value.enabled_tooltip
