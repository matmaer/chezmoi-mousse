"""Contains StrEnum classes without other dependencies."""

from enum import StrEnum, auto

__all__ = [
    "Chars",
    "ContainerName",
    "DataTableName",
    "LogName",
    "PathKind",
    "ScreenName",
    "TabName",
    "Tcss",
    "TreeName",
    "ViewName",
]


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
    canvas = auto()
    config_switcher = auto()
    dest_dir_info = auto()
    doctor = auto()
    git_log_global = auto()
    git_log_path = auto()
    help_switcher = auto()
    init_screen_switcher = auto()
    left_side = auto()
    logs_switcher = auto()
    operate_btn_group = auto()
    post_operate = auto()
    pre_operate = auto()
    right_side = auto()
    switch_slider = auto()
    switcher_btn_group = auto()
    tree_switcher = auto()
    view_switcher = auto()


class DataTableName(StrEnum):
    apply_git_log_table = auto()
    doctor_table = auto()
    git_global_log_table = auto()
    re_add_git_log_table = auto()


class LogName(StrEnum):
    """Names for RichLog widgets."""

    app_logger = auto()
    contents_logger = auto()
    debug_logger = auto()
    diff_logger = auto()
    operate_logger = auto()
    read_logger = auto()
    splash_logger = auto()


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


class Tcss(StrEnum):
    border_title_top = ".border_title_top"
    changes_enabled_color = ".changes_enabled_color"
    content_switcher_left = ".content_switcher_left"
    custom_collapsible = ".custom_collapsible"
    dir_tree_widget = ".dir_tree_widget"
    doctor_table = ".doctor_table"
    flat_button = ".flat_button"
    flat_link = ".flat_link"
    flow_diagram = ".flow_diagram"
    install_help = ".install_help"
    last_clicked = ".last_clicked"
    operate_button = ".operate_button"
    pw_mgr_group = ".pw_mgr_group"
    read_cmd_static = ".read_cmd_static"
    single_button_vertical = ".single_button_vertical"
    tab_button = ".tab_button"
    tab_left_vertical = ".tab_left_vertical"
    tree_widget = ".tree_widget"
    input_select = ".input_select"
    input_field = ".input_field"


class TreeName(StrEnum):
    add_tree = auto()
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
