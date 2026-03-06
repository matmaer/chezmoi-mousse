from enum import StrEnum

__all__ = [
    "BindingDescription",
    "BorderTitle",
    "Chars",
    "FlatBtnLabel",
    "LinkBtn",
    "LogString",
    "OperateString",
    "SectionLabel",
    "StatusCode",
    "SwitchLabel",
    "TabLabel",
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
    refresh_tree = "Refresh Tree"
    template_data = "Template Data"
    test_paths = "Test Paths"
    memory_usage = "Memory Usage"


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


class TabLabel(StrEnum):
    # Main tabs
    add = "Add"
    apply = "Apply"
    config = "Config"
    debug = "Debug"
    help = "Help"
    logs = "Logs"
    re_add = "Re-Add"
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


class BorderTitle(StrEnum):
    app_log = " Application Log "
    cmd_log = " Chezmoi Commands Log "
    debug_log = " Debug Log "
    memory_usage = " Memory Usage "
    dest_dir = " destDir "
    dom_nodes = " DOM Nodes "
    global_git_log = " Global Chezmoi Git Log "
    list_tree = dest_dir + "files "
    test_paths = " Test Paths "


class Chars(StrEnum):
    # bullet = "\u2022"  # BULLET # noqa: ERA001
    burger = "\u2261"  # IDENTICAL TO
    check_mark = "\u2714"  # HEAVY CHECK MARK
    down_triangle = "\u25be"  # BLACK DOWN-POINTING SMALL TRIANGLE
    # gear = "\u2699"  # GEAR # noqa: ERA001
    lower_3_8ths_block = "\u2583"  # LOWER THREE EIGHTHS BLOCK
    right_arrow = f"{'\u2014' * 3}\u2192"  # EM DASH, RIGHTWARDS ARROW
    right_triangle = "\u25b8"  # BLACK RIGHT-POINTING SMALL TRIANGLE
    # Used for Tree widgets
    tree_collapsed = f"{right_triangle} "
    tree_expanded = f"{down_triangle} "
    warning_sign = "\u26a0"  # WARNING SIGN
    x_mark = "\u2716"  # HEAVY MULTIPLICATION X


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


class BindingDescription(StrEnum):
    # Tab bindings
    hide_filters = "Hide filters"
    # Shared bindings
    maximize = "Maximize"
    minimize = "Minimize"
    show_filters = "Show filters"
    toggle_dry_run = "Toggle --dry-run"


class SwitchLabel(StrEnum):
    expand_all = "Expand all dirs"
    init_repo = "Init existing repo"
    unchanged = "Show unchanged paths"
    unmanaged_dirs = "Show unmanaged dirs"
    unwanted = "Show unwanted paths"


class OperateString(StrEnum):
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
    # Init screen info strings
    guess_https = "Let chezmoi guess the best URL to clone from."
    guess_ssh = "Let chezmoi guess the best ssh scp-style address to clone from."
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


class SectionLabel(StrEnum):
    cat_config_output = "Cat Config Output"
    doctor_output = "Doctor Output"
    ignored_output = "Ignored Output"
    init_new_repo = "Initialize New Chezmoi Repository"
    # init_clone_repo = "Initialize Existing Chezmoi Repository" # noqa: ERA001
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
    No_Status = "X"
    Run = "R"  # not implemented TODO: disable operate buttons
    # Fake X status: managed paths absent from chezmoi status output
