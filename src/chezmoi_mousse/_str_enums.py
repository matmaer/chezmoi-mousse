from enum import StrEnum, auto

__all__ = [
    "BindingAction",
    "BindingDescription",
    "Chars",
    "ContainerName",
    "FlatBtnLabel",
    "RichLogName",
    "LogString",
    "OperateString",
    "SectionLabel",
    "StatusCode",
    "SwitchLabel",
    "TabLabel",
    "Tcss",
]


class BindingAction(StrEnum):
    toggle_dry_run = auto()
    toggle_maximized = auto()
    toggle_switch_slider = auto()


class ContainerName(StrEnum):
    cat_config = auto()
    contents = auto()
    debug_log = auto()
    diagram = auto()
    diff = auto()
    doctor = auto()
    dom_nodes = auto()
    git_ignored = auto()
    git_log = auto()
    left_side = auto()
    memory_usage = auto()
    operate_buttons = auto()
    pw_mgr_info = auto()
    right_side = auto()
    template_data = auto()
    test_paths_view = auto()


class RichLogName(StrEnum):
    app_logger = auto()
    cmd_logger = auto()
    debug_logger = auto()
    dom_node_logger = auto()
    memory_usage_logger = auto()


class Tcss(StrEnum):
    added = auto()
    changed = auto()
    changes_enabled_color = auto()
    context = auto()
    dest_dir_tree_label = auto()
    flat_button = auto()
    flat_section_label = auto()
    flow_diagram = auto()
    full_cmd = auto()
    info = auto()
    last_clicked_flat_btn = auto()
    last_clicked_tab_btn = auto()
    limited_label = auto()
    main_section_label = auto()
    managed_tree = auto()
    operate_button = auto()
    operate_info = auto()
    pw_mgr_group = auto()
    refresh_button = auto()
    removed = auto()
    single_button_vertical = auto()
    sub_section_label = auto()
    tab_button = auto()
    tab_left_vertical = auto()
    unhandled = auto()

    # add a property to return the name with a dot prefix
    @property
    def dot_prefix(self) -> str:
        return f".{self.value}"


class FlatBtnLabel(StrEnum):
    cat_config = "Cat Config"
    debug_log = "Debug Log"
    diagram = "Diagram"
    doctor = "Doctor"
    dom_nodes = "DOM Nodes"
    ignored = "Ignored"
    pw_mgr_info = "Password Managers"
    template_data = "Template Data"
    test_paths = "Test Paths"
    memory_usage = "Memory Usage"


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
    debug_tab_enabled = "Debug tab enabled"
    doctor_errors_found = "One or more errors found"
    doctor_fails_found = "One or more tests failed"
    doctor_no_issue_found = "No warnings, failed or error entries found"
    doctor_warnings_found = "Only warnings found, probably safe to ignore"
    no_stderr = "No output on stderr"
    no_stdout = "No output on stdout"
    using_chezmoi_bin = "Using chezmoi binary at:"


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
