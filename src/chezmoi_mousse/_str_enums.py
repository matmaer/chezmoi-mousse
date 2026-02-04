"""Contains StrEnum classes without other dependencies."""

from enum import StrEnum

__all__ = [
    "BindingDescription",
    "Chars",
    "FlatBtnLabel",
    "LinkBtn",
    "LogString",
    "OpBtnLabel",
    "OperateString",
    "SectionLabel",
    "StatusCode",
    "SwitchLabel",
    "SubTabLabel",
]

#########################################
# StrEnum classes for buttons and links #
#########################################


class FlatBtnLabel(StrEnum):
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
        return self.value.replace("https://", "").replace("www.", "").rstrip("/")


class SubTabLabel(StrEnum):
    # Tab buttons for content switcher within a main tab
    app_log = "App"
    cmd_log = "Chezmoi Commands"
    contents = "Contents"
    diff = "Diff"
    git_log = "Git-Log"
    list = "List"
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


class LogString(StrEnum):
    app_log_initialized = "Application log initialized"
    chezmoi_found = "Found chezmoi command"
    chezmoi_not_found = "chezmoi command not found"
    cmd_log_initialized = "Chezmoi commands log initialized"
    debug_log_initialized = "Debug log initialized"
    dev_mode_enabled = "Dev mode enabled"
    doctor_errors_found = "One or more errors found"
    doctor_fails_found = "One or more tests failed"
    doctor_no_issue_found = "No warnings, failed or error entries found"
    doctor_warnings_found = "Only warnings found, probably safe to ignore"
    no_stderr = "No output on stderr"
    no_stdout = "No output on stdout"
    see_config_tab = "See the Config tab for the doctor command output."
    std_err_logged = "Command stderr available in an Output log view"
    succes_no_output = f"Success, {no_stdout.lower()}"
    success_with_output = "Success, output will be processed"
    verify_exit_zero = "All targets match their target state"
    verify_non_zero = "Not all targets match their target state"


class OpBtnLabel(StrEnum):
    add_review = "Review Add Path"
    add_run = "Run Chezmoi Add"
    apply_review = "Review Apply Path"
    apply_run = "Run Chezmoi Apply"
    cancel = "Cancel"
    create_paths = "(Re)Create Test Paths"
    destroy_review = "Review Destroy Path"
    destroy_run = "Run Chezmoi Destroy"
    exit_app = "Exit App"
    forget_review = "Review Forget Path"
    forget_run = "Run Chezmoi Forget"
    init_review = "Review Init Chezmoi"
    init_run = "Run Chezmoi Init"
    re_add_review = "Review Re-Add Path"
    re_add_run = "Run Chezmoi Re-Add"
    reload = "Reload"
    remove_paths = "Remove Test Paths"
    toggle_diffs = "Toggle Diffs"


class BindingDescription(StrEnum):
    # Screen bindings
    cancel = OpBtnLabel.cancel
    reload = OpBtnLabel.reload
    # Tab bindings
    hide_filters = "Hide filters"
    show_filters = "Show filters"
    # Shared bindings
    toggle_dry_run = "Toggle --dry-run"
    maximize = "Maximize"
    minimize = "Minimize"


class SwitchLabel(StrEnum):
    init_repo = "Init existing repo"
    expand_all = "Expand all dirs"
    unchanged = "Show unchanged files"
    unmanaged_dirs = "Show unmanaged dirs"
    unwanted = "Show unwanted paths"


class OperateString(StrEnum):
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
    # read_file = "[$success]Path.read()[/]"
    ready_to_run = "[$text]Ready to run[/]"
    re_add_path_info = (
        "[dim]Re-add modified files in the target state, preserving "
        "any encrypted_ attributes. chezmoi will not overwrite templates, and "
        "all entries that are not files are ignored. If adding a directory, it"
        " will be recursed in.[/]"
    )
    re_add_subtitle = f"path on disk {Chars.right_arrow} overwrite chezmoi repo"
    # Init screen info strings
    guess_https = "Let chezmoi guess the best URL to clone from."
    guess_ssh = "Let chezmoi guess the best ssh scp-style address to clone from."
    init_new_info = (
        "Ready to initialize a new chezmoi repository. Toggle the "
        "[$foreground-darken-1 on $surface-lighten-1] "
        f"{SwitchLabel.init_repo} [/]"
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


class SectionLabel(StrEnum):
    cat_config_output = "Cat Config Output"
    doctor_output = "Doctor Output"
    ignored_output = "Ignored Output"
    init_new_repo = "Initialize New Chezmoi Repository"
    # init_clone_repo = "Initialize Existing Chezmoi Repository"
    password_managers = "Password Manager Information"
    pre_init_cmd_output = "Pre-init Command Outputs"
    project_description = "Project Description"
    project_link = "Project Link"
    stderr_output = "Output from stderr"
    stdout_output = "Output from stdout"
    template_data_output = "Chezmoi Data Output"


class StatusCode(StrEnum):
    # Real status codes from chezmoi
    Added = "A"
    Deleted = "D"
    Modified = "M"
    No_Change = " "
    Run = "R"  # not implemented TODO: disable operate buttons
    X = "X"  # Fake X status: managed paths absent from chezmoi status output
