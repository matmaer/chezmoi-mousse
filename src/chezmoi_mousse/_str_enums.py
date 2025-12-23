"""Contains StrEnum classes without other dependencies."""

from enum import StrEnum

from ._chezmoi import ReadCmd
from ._switch_data import Switches

__all__ = [
    "Chars",
    "DestDirStrings",
    "FlatBtn",
    "LinkBtn",
    "LogStrings",
    "OperateStrings",
    "SectionLabels",
    "TabBtn",
]

#########################################
# StrEnum classes for buttons and links #
#########################################


class FlatBtn(StrEnum):
    add_help = "Add Help"
    apply_help = "Apply Help"
    cat_config = "Cat Config"
    diagram = "Diagram"
    doctor = "Doctor"
    exit_app = "Exit App"
    ignored = "Ignored"
    pw_mgr_info = "Password Managers"
    re_add_help = "Re-Add Help"
    template_data = "Template Data"


class LinkBtn(StrEnum):
    chezmoi_add = "https://www.chezmoi.io/reference/commands/add/"
    chezmoi_apply = "https://www.chezmoi.io/reference/commands/apply/"
    chezmoi_destroy = "https://www.chezmoi.io/reference/commands/destroy/"
    chezmoi_forget = "https://www.chezmoi.io/reference/commands/forget/"
    chezmoi_guess = "https://www.chezmoi.io/reference/commands/init/"
    chezmoi_install = "https://www.chezmoi.io/install/"
    chezmoi_re_add = "https://www.chezmoi.io/reference/commands/re-add/"

    @property
    def link_url(self) -> str:
        return self.value

    @property
    def link_text(self) -> str:
        if self.value == LinkBtn.chezmoi_guess.value:
            return "guess info"
        return (
            self.value.replace("https://", "").replace("www.", "").rstrip("/")
        )


class TabBtn(StrEnum):
    # Tab buttons for content switcher within a main tab
    app_log = "App"
    contents = "Contents"
    debug_log = "Debug"
    diff = "Diff"
    git_log_global = "Git"
    git_log_path = "Git-Log"
    list = "List"
    operate_log = "Operate"
    read_log = "Read"
    tree = "Tree"


#########################
# Other StrEnum classes #
#########################


class Chars(StrEnum):
    bullet = "\u2022"  # BULLET
    burger = "\u2261"  # IDENTICAL TO
    check_mark = "\u2714"  # HEAVY CHECK MARK
    down_triangle = "\u25be "  # BLACK DOWN-POINTING SMALL TRIANGLE
    # gear = "\u2699"  # GEAR
    lower_3_8ths_block = "\u2583"  # LOWER THREE EIGHTHS BLOCK
    right_arrow = f"{'\u2014' * 3}\u2192"  # EM DASH, RIGHTWARDS ARROW
    right_triangle = "\u25b8 "  # BLACK RIGHT-POINTING SMALL TRIANGLE
    warning_sign = "\u26a0"  # WARNING SIGN
    x_mark = "\u2716"  # HEAVY MULTIPLICATION X


class LogStrings(StrEnum):
    app_log_initialized = "Application log initialized"
    debug_log_initialized = "Debug log initialized"
    chezmoi_found = "Found chezmoi command"
    chezmoi_not_found = "chezmoi command not found"
    dev_mode_enabled = "Dev mode enabled"
    operate_log_initialized = "Operate log initialized"
    read_log_initialized = "Read command log initialized"


class OperateStrings(StrEnum):
    add_path = (
        "[$text-primary]The path will be added to the chezmoi source state.[/]"
    )
    add_subtitle = f"path on disk {Chars.right_arrow} chezmoi repo"
    apply_path = (
        "[$text-primary]The path in the destination directory will be "
        "modified.[/]"
    )
    apply_subtitle = f"chezmoi repo {Chars.right_arrow} path on disk"
    auto_commit = (
        f"[$text-warning]{Chars.warning_sign} Auto commit is enabled: "
        "files will also be committed."
        f"{Chars.warning_sign}[/]"
    )
    auto_push = (
        f"[$text-warning]{Chars.warning_sign} Auto push is enabled: "
        "files will be pushed to the remote."
        f"{Chars.warning_sign}[/]"
    )
    cmd_output_subtitle = "Command Output"
    destroy_path = (
        "[$text-error]Permanently remove the path from disk and "
        " chezmoi. MAKE SURE YOU HAVE A BACKUP![/]"
    )
    destroy_subtitle = (
        f"{Chars.x_mark} delete on disk and in chezmoi repo {Chars.x_mark}"
    )
    diff_color = (
        f"[$text-success]+ green lines will be added[/]\n"
        "[$text-error]- red lines will be removed[/]\n"
        f"[dim]{Chars.bullet} dimmed lines for context[/]"
    )
    error_subtitle = "Operation failed with errors"
    forget_path = (
        "[$text-primary]Remove the path from the source state, i.e. stop "
        "managing them.[/]"
    )
    forget_subtitle = (
        f"{Chars.x_mark} leave on disk but remove from chezmoi repo "
        f"{Chars.x_mark}"
    )
    guess_https = "Let chezmoi guess the best URL to clone from."
    guess_ssh = (
        "Let chezmoi guess the best ssh scp-style address to clone from."
    )
    https_url = (
        "Enter a complete URL, e.g., "
        "[$text-primary]https://github.com/user/repo.git[/]. "
        "If you have a PAT, make sure to include it in the URL, for example: "
        "[$text-primary]https://username:ghp_123456789abcdef@github.com/"
        "username/my-dotfiles.git[/] and delete the PAT after use."
    )
    init_new_info = (
        "Ready to initialize a new chezmoi repository. Toggle the "
        "[$foreground-darken-1 on $surface-lighten-1] "
        f"{Switches.init_repo_switch.label} [/]"
        "switch to initialize by cloning an existing Github repository."
    )
    read_file = "[$success]Path.read()[/]"
    re_add_path = (
        "[$text-primary]Overwrite the source state with current local path.[/]"
    )
    re_add_subtitle = (
        f"path on disk {Chars.right_arrow} overwrite chezmoi repo"
    )
    ssh_select = (
        "Enter an SSH SCP-style URL, e.g., "
        "[$text_primary]git@github.com:user/repo.git[/]. If the repository is"
        "private, make sure you have your SSH key pair set up before using "
        "this option."
    )
    success_subtitle = "Operation completed successfully"


class DestDirStrings(StrEnum):
    _click_file = "Click a file to see the output from "
    _click_dir = "Click a directory to see"
    add = (
        "Click a directory to see if it's managed or unmanaged, "
        "and if it contains files to add.\n"
        f"{_click_file}{OperateStrings.read_file}."
    )
    cat = f"{_click_file}[$success]{ReadCmd.cat.pretty_cmd}[/]."
    diff = f"{_click_file}[$success]{ReadCmd.diff.pretty_cmd}[/]."
    diff_reverse = (
        f"{_click_file}[$success]{ReadCmd.diff_reverse.pretty_cmd}[/]."
    )
    git_log_msg = (
        f"Click a path to see the output from "
        f"[$success]{ReadCmd.git_log.pretty_cmd}[/]."
    )
    re_add = f"{_click_file}[$success]{OperateStrings.read_file}[/]."


class SectionLabels(StrEnum):
    """Strings used for textual Label classes except for the help_tab.py module
    which has its own StrEnum class "HelpSections" and the install_help.py
    module which has its own StrEnum class "InstallHelpStrings"."""

    file_read_output = "File Contents"
    cat_config_output = "Cat Config Output"
    contents_info = "Contents Info"
    debug_log_output = "Debug Log Output"
    diff_info = "Diff Info"
    doctor_output = "Doctor Output"
    ignored_output = "Ignored Output"
    init_new_repo = "Initialize New Chezmoi Repository"
    operate_output = "Operate Command Output"
    password_managers = "Password Manager Information"
    pre_init_cmd_output = "Pre-init Command Outputs"
    project_description = "Project Description"
    project_link = "Project Link"
    template_data_output = "Chezmoi Data Output"
