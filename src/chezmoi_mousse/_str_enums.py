"""Contains StrEnum classes without other dependencies."""

from enum import StrEnum

from ._switch_data import Switches

__all__ = [
    "Chars",
    "FlatBtn",
    "LinkBtn",
    "LogStrings",
    "OperateStrings",
    "SectionLabels",
    "StatusCode",
    "TabBtn",
]

#########################################
# StrEnum classes for buttons and links #
#########################################


class FlatBtn(StrEnum):
    add_help = "Add Help"
    apply_help = "Apply Help"
    cat_config = "Cat Config"
    debug_log = "Debug Log"
    diagram = "Diagram"
    doctor = "Doctor"
    dom_nodes = "DOM Nodes"
    exit_app = "Exit App"
    ignored = "Ignored"
    pw_mgr_info = "Password Managers"
    re_add_help = "Re-Add Help"
    template_data = "Template Data"
    test_paths = "Test Paths"


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
    # bullet = "\u2022"  # BULLET
    burger = "\u2261"  # IDENTICAL TO
    check_mark = "\u2714"  # HEAVY CHECK MARK
    down_triangle = "\u25be"  # BLACK DOWN-POINTING SMALL TRIANGLE
    # gear = "\u2699"  # GEAR
    lower_3_8ths_block = "\u2583"  # LOWER THREE EIGHTHS BLOCK
    right_arrow = f"{'\u2014' * 3}\u2192"  # EM DASH, RIGHTWARDS ARROW
    right_triangle = "\u25b8"  # BLACK RIGHT-POINTING SMALL TRIANGLE
    warning_sign = "\u26a0"  # WARNING SIGN
    x_mark = "\u2716"  # HEAVY MULTIPLICATION X
    # Used for Tree widgets
    tree_collapsed = f"{right_triangle} "
    tree_expanded = f"{down_triangle} "


class LogStrings(StrEnum):
    app_log_initialized = "Application log initialized"
    debug_log_initialized = "Debug log initialized"
    chezmoi_found = "Found chezmoi command"
    chezmoi_not_found = "chezmoi command not found"
    dev_mode_enabled = "Dev mode enabled"
    operate_log_initialized = "Operate log initialized"
    read_log_initialized = "Read command log initialized"


class OperateStrings(StrEnum):
    add_path_info = (
        "[dim]Add new targets to the source state. If adding a directory, it"
        " will be recursed in.[/]"
    )
    add_subtitle = f"local path {Chars.right_arrow} chezmoi repo"
    apply_subtitle = f"chezmoi repo {Chars.right_arrow} path on disk"
    apply_path_info = (
        "[dim]Chezmoi will ensure that the path is in the target state. "
        "The command will run without prompting. "
        "For targets modified since chezmoi last wrote it. If adding a "
        "directory, it will be recursed in.[/]"
    )
    auto_commit = (
        f"[$text-warning]{Chars.warning_sign} Git auto commit is enabled: "
        "files will also be committed."
        f"{Chars.warning_sign}[/]"
    )
    auto_push = (
        f"[$text-warning]{Chars.warning_sign} Git auto push is enabled: "
        "files will be pushed to the remote."
        f"{Chars.warning_sign}[/]"
    )
    in_dest_dir_click_path = "<- Select a file or directory to operate on."
    destroy_path_info = (
        "[$text-error]Permanently remove the path from disk and chezmoi. MAKE "
        "SURE YOU HAVE A BACKUP![/]"
    )
    destroy_subtitle = (
        f"[$text-error]{Chars.x_mark}[/] delete on disk and in chezmoi repo "
        f"[$text-error]{Chars.x_mark}[/]"
    )
    forget_path_info = (
        "[dim]Remove from the source state, i.e. stop managing them.[/]"
    )
    forget_subtitle = (
        f"leave on disk {Chars.right_arrow} chezmoi repo {Chars.x_mark}"
    )
    # read_file = "[$success]Path.read()[/]"
    ready_to_run = "[$text]Ready to run[/]"
    re_add_path_info = (
        "[dim]Re-add modified files in the target state, preserving "
        "any encrypted_ attributes. chezmoi will not overwrite templates, and "
        "all entries that are not files are ignored. If adding a directory, it"
        " will be recursed in.[/]"
    )
    re_add_subtitle = (
        f"path on disk {Chars.right_arrow} overwrite chezmoi repo"
    )
    no_stdout_write_cmd_live = (
        "No output on stdout, the command was executed live, i.e. "
        "without --dry-run flag."
    )
    no_stdout_write_cmd_dry = (
        "No output on stdout, the command was executed "
        " with the --dry-run flag."
    )
    no_stderr_write_cmd_live = (
        "No output on stderr, the command was executed live, i.e. "
        "without --dry-run flag."
    )
    no_stderr_write_cmd_dry = (
        "No output on stderr, the command was executed "
        " with the --dry-run flag."
    )
    # Init screen info strings
    guess_https = "Let chezmoi guess the best URL to clone from."
    guess_ssh = (
        "Let chezmoi guess the best ssh scp-style address to clone from."
    )
    init_new_info = (
        "Ready to initialize a new chezmoi repository. Toggle the "
        "[$foreground-darken-1 on $surface-lighten-1] "
        f"{Switches.init_repo_switch.label} [/]"
        "switch to initialize by cloning an existing Github repository."
    )
    https_url = (
        "Enter a complete URL, e.g., "
        "[$text-primary]https://github.com/user/repo.git[/]. "
        "If you have a PAT, make sure to include it in the URL, for example: "
        "[$text-primary]https://username:ghp_123456789abcdef@github.com/"
        "username/my-dotfiles.git[/] and delete the PAT after use."
    )
    ssh_select = (
        "Enter an SSH SCP-style URL, e.g., "
        "[$text_primary]git@github.com:user/repo.git[/]. If the repository is"
        "private, make sure you have your SSH key pair set up before using "
        "this option."
    )
    init_subtitle = "initialize chezmoi repository"


class SectionLabels(StrEnum):
    """Strings used for textual Label classes except for the help_tab.py module
    which has its own StrEnum class "HelpSections" and the install_help.py
    module which has its own StrEnum class "InstallHelpStrings"."""

    file_read_output = "File Contents"
    cat_config_output = "Cat Config Output"
    contents_info = "Contents Info"
    diff_info = "Diff Info"
    doctor_output = "Doctor Output"
    ignored_output = "Ignored Output"
    init_new_repo = "Initialize New Chezmoi Repository"
    # init_clone_repo = "Initialize Existing Chezmoi Repository"
    password_managers = "Password Manager Information"
    pre_init_cmd_output = "Pre-init Command Outputs"
    project_description = "Project Description"
    project_link = "Project Link"
    template_data_output = "Chezmoi Data Output"


class StatusCode(StrEnum):
    # Real status codes from chezmoi
    Added = "A"
    Deleted = "D"
    Modified = "M"
    No_Change = " "
    # Run = "R" TODO: implement
    # Fake status codes for internal use
    fake_dest_dir = "F"  # used for destDir path
    # fake_status = "S"  # used for re-add dir paths
    fake_no_status = "X"  # (no status depending on apply or re-add context)
    # fake_unmanaged = "U"
