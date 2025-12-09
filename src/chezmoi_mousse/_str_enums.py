"""Contains StrEnum classes without other dependencies."""

from enum import StrEnum, auto

from ._chezmoi import ReadCmd

__all__ = [
    "BindingAction",
    "BindingDescription",
    "Chars",
    "ContainerName",
    "ContentSwitcherName",
    "DataTableName",
    "DestDirStrings",
    "HeaderTitle",
    "LogName",
    "LogText",
    "PathKind",
    "ScreenName",
    "SectionLabels",
    "TabName",
    "Tcss",
    "TreeName",
    "ViewName",
]


class BindingAction(StrEnum):
    exit_screen = auto()
    toggle_dry_run = auto()
    toggle_maximized = auto()
    toggle_switch_slider = auto()


class BindingDescription(StrEnum):
    # Screen bindings
    cancel = "Cancel"
    close = "Close"
    exit_app = "Exit App"
    reload = "Close & Reload"
    # Tab bindings
    hide_filters = "Hide filters"
    show_filters = "Show filters"
    # Shared bindings
    add_dry_run_flag = "Add --dry-run flag"
    maximize = "Maximize"
    minimize = "Minimize"
    remove_dry_run_flag = "Remove --dry-run flag"


class Chars(StrEnum):
    add_info_border = f"local {'\u2014' * 3}\u2192 chezmoi"  # '\N{EM DASH}', '\N{RIGHTWARDS ARROW}'
    apply_info_border = f"local \u2190{'\u2014' * 3} chezmoi"  # '\N{LEFTWARDS ARROW}', '\N{EM DASH}'
    bullet = "\u2022"  # '\N{BULLET}'
    burger = "\u2261"  # '\N{IDENTICAL TO}'
    check_mark = "\u2714"  # '\N{HEAVY CHECK MARK}'
    destroy_info_border = "\u274c destroy \u274c"  # '\N{CROSS MARK}'
    down_triangle = "\u25be "  # '\N{BLACK DOWN-POINTING SMALL TRIANGLE}'DOWN-POINTING TRIANGLE}'
    forget_info_border = "\u2716 forget \u2716"  # '\N{HEAVY MULTIPLICATION X}'
    # gear = "\u2699"  # '\N{GEAR}'
    lower_3_8ths_block = "\u2583"  # "\N{LOWER THREE EIGHTHS BLOCK}"
    re_add_info_border = f"local {'\u2014' * 3}\u2192 chezmoi"  # '\N{EM DASH}', '\N{RIGHTWARDS ARROW}'
    right_triangle = "\u25b8 "  # '\N{BLACK RIGHT-POINTING SMALL TRIANGLE}'
    warning_sign = "\u26a0"  # '\N{WARNING SIGN}'
    x_mark = "\u2716"  # '\N{HEAVY MULTIPLICATION X}'


class ContainerName(StrEnum):
    contents = auto()
    dest_dir_info = auto()
    diff = auto()
    doctor = auto()
    git_log_global = auto()
    git_log_path = auto()
    left_side = auto()
    operate_buttons = auto()
    post_operate = auto()
    pre_operate = auto()
    right_side = auto()
    switch_slider = auto()


class ContentSwitcherName(StrEnum):
    apply_tree_buttons = auto()
    apply_tree_switcher = auto()
    apply_view_buttons = auto()
    apply_view_switcher = auto()
    config_switcher = auto()
    help_switcher = auto()
    init_screen_switcher = auto()
    logs_switcher = auto()
    logs_tab_buttons = auto()
    re_add_tree_buttons = auto()
    re_add_tree_switcher = auto()
    re_add_view_buttons = auto()
    re_add_view_switcher = auto()
    re_add_views_vertical = auto()


class DataTableName(StrEnum):
    doctor_table = auto()
    git_log_table = auto()


class DestDirStrings(StrEnum):
    _cat_prefix = (
        "Click a file or directory in the tree to see the output from"
    )
    _diff_prefix = "Click a path to see the output from"
    _git_log_prefix = "Click a path in the tree to see the output from"
    cat = f'{_cat_prefix} [$success]"{ReadCmd.cat.pretty_cmd}"[/].'
    diff = f'{_diff_prefix} [$success]"{ReadCmd.diff.pretty_cmd}"[/].'
    diff_reverse = (
        f'{_diff_prefix} [$success]"{ReadCmd.diff_reverse.pretty_cmd}"[/].'
    )
    dir_info = "Click a directary to see if it's managed or unmanaged."
    git_log_msg = (
        f'{_git_log_prefix} [$success]"{ReadCmd.git_log.pretty_cmd}"[/].'
    )
    in_dest_dir = "This is the destination directory (chezmoi destDir)"
    read_file = (
        'Click a file to see the output from [$success]"Path.read()"[/].'
    )


class HeaderTitle(StrEnum):
    header_dry_run_mode = (
        " -  c h e z m o i  m o u s s e  --  d r y  r u n  m o d e  - "
    )
    header_live_mode = (
        " -  c h e z m o i  m o u s s e  --  l i v e  m o d e  - "
    )
    header_install_help = (
        " - c h e z m o i  m o u s s e  --  i n s t a l l  h e l p  - "
    )


class LogName(StrEnum):
    """Names for RichLog widgets."""

    app_logger = auto()
    contents_logger = auto()
    debug_logger = auto()
    diff_logger = auto()
    operate_logger = auto()
    read_logger = auto()
    splash_logger = auto()


class LogText(StrEnum):
    app_log_initialized = "Application log initialized"
    debug_log_initialized = "Debug log initialized"
    chezmoi_found = "Found chezmoi command"
    chezmoi_not_found = "chezmoi command not found"
    dev_mode_enabled = "Dev mode enabled"
    operate_log_initialized = "Operate log initialized"
    read_log_initialized = "Read command log initialized"


class PathKind(StrEnum):
    DIR = auto()
    FILE = auto()


class ScreenName(StrEnum):
    init = auto()
    install_help = auto()
    main = auto()
    operate = auto()
    splash = auto()


class TabName(StrEnum):
    add = auto()
    apply = auto()
    config = auto()
    help = auto()
    logs = auto()
    re_add = auto()


class SectionLabels(StrEnum):
    cat_config_output = '"chezmoi cat-config" output'
    debug_log_output = "Debug Log Output"
    doctor_output = '"chezmoi doctor" output'
    ignored_output = '"chezmoi ignored" output'
    init_clone_repo = "Initialize from an existing repository"
    init_clone_repo_url = "Repository URL to clone from."
    init_new_repo = "Initialize a new chezmoi repository"
    operate_context = "Operate Context"
    operate_output = "Operate Command Output"
    password_managers = "Password Manager Information"
    path_info = "Path Information"
    project_description = "Project Description"
    project_link = "Project Link"
    template_data_output = '"chezmoi data" output'


class Tcss(StrEnum):
    border_title_top = auto()
    changes_enabled_color = auto()
    content_switcher_left = auto()
    doctor_table = auto()
    flat_button = auto()
    flat_link = auto()
    flow_diagram = auto()
    input_field = auto()
    input_select = auto()
    last_clicked_flat_btn = auto()
    last_clicked_tab_btn = auto()
    operate_button = auto()
    pw_mgr_group = auto()
    read_cmd_static = auto()
    single_button_vertical = auto()
    tab_button = auto()
    tab_left_vertical = auto()
    tree_widget = auto()

    # add a property to return the name with a dot prefix
    @property
    def dot_prefix(self) -> str:
        return f".{self.value}"


class TreeName(StrEnum):
    dir_tree = auto()
    expanded_tree = auto()
    list_tree = auto()
    managed_tree = auto()


class ViewName(StrEnum):
    add_help_view = auto()
    apply_help_view = auto()
    cat_config_view = auto()
    diagram_view = auto()
    git_ignored_view = auto()
    init_clone_view = auto()
    init_new_view = auto()
    pw_mgr_info_view = auto()
    re_add_help_view = auto()
    template_data_view = auto()
