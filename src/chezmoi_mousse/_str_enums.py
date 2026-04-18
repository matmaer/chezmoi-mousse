from enum import StrEnum

__all__ = [
    "BindingDescription",
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
    cat_config = "Cat Config"
    debug_log = "Debug Log"
    diagram = "Diagram"
    doctor = "Doctor"
    dom_nodes = "DOM Nodes"
    exit_app = "Exit App"
    ignored = "Ignored"
    pw_mgr_info = "Password Managers"
    template_data = "Template Data"
    test_paths = "Test Paths"
    memory_usage = "Memory Usage"


class LinkBtn(StrEnum):
    chezmoi_install = "https://www.chezmoi.io/install/"

    @property
    def link_url(self) -> str:
        return self.value

    @property
    def link_text(self) -> str:
        return self.value.replace("https://", "").replace("www.", "").rstrip("/")


class TabLabel(StrEnum):
    # Main tabs
    add = "Add"
    apply = "Apply"
    config = "Config"
    debug = "Debug"
    logs = "Logs"
    re_add = "Re-Add"
    # Tab buttons for content switcher within a main tab
    app_log = "Application"
    cmd_log = "Chezmoi-Commands"
    contents = "Contents"
    diff = "Diff"
    git_log = "Git-Log"

    @classmethod
    def main_tabs(cls) -> tuple["TabLabel", ...]:
        return (cls.apply, cls.re_add, cls.add, cls.logs, cls.config, cls.debug)


#########################
# Other StrEnum classes #
#########################


class Chars(StrEnum):
    # bullet = "\u2022"  # BULLET # noqa: ERA001
    burger = "\u2261"  # IDENTICAL TO
    # check_mark = "\u2714"  # HEAVY CHECK MARK # noqa: ERA001
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
    debug_log_initialized = "Debug log initialized"
    dev_mode_enabled = "Dev mode enabled"
    doctor_errors_found = "One or more errors found"
    doctor_fails_found = "One or more tests failed"
    doctor_no_issue_found = "No warnings, failed or error entries found"
    doctor_warnings_found = "Only warnings found, probably safe to ignore"
    no_stderr = "No output on stderr"
    no_stdout = "No output on stdout"
    using_chezmoi_bin = "Using chezmoi binary at:"
    verify_exit_zero = "All targets match their target state, no diffs available"
    verify_non_zero = "Not all targets match their target state, diffs are available"


class BindingDescription(StrEnum):
    # Tab bindings
    hide_filters = "Hide filters"
    # Shared bindings
    maximize = "Maximize"
    minimize = "Minimize"
    show_filters = "Show filters"
    remove_dry_run = "Remove --dry-run"
    add_dry_run = "Add --dry-run"


class SwitchLabel(StrEnum):
    expand_all = "Expand all dirs"
    unchanged = "Show unchanged paths"
    managed_dirs = "Hide unmanaged dirs"
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


class SectionLabel(StrEnum):
    cat_config_output = "Cat Config Output"
    debug_log = " Debug Log "
    diagram = "Chezmoi Diagram"
    doctor_output = "Doctor Output"
    dom_nodes = " DOM Nodes "
    full_cmd = "Full Command"
    ignored_output = "Ignored Output"
    memory_usage = " Memory Usage "
    password_managers = "Password Manager Information"
    paths_with_status = "Paths with Status"
    project_description = "Project Description"
    project_link = "Project Link"
    stderr_output = "Output from stderr"
    stdout_output = "Output from stdout"
    template_data_output = "Chezmoi Data Output"
    test_paths = " Test Paths "


class StatusCode(StrEnum):
    Added = "A"
    Deleted = "D"
    Modified = "M"
    Run = "R"
    Space = " "

    @property
    def _theme_var_color_name(self) -> dict[str, str]:
        return {
            StatusCode.Added: "text-success",
            StatusCode.Deleted: "text-error",
            StatusCode.Modified: "text-warning",
            StatusCode.Run: "text-error",  # choose error as it's not yet implemented
            StatusCode.Space: "text-muted",
        }

    @property
    def color_var(self) -> str:
        return self._theme_var_color_name[self.value]

    @property
    def color_tag(self) -> str:
        # return the color for a status code
        return f"[${self.color_var}]"
