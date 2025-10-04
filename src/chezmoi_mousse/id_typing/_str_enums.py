"""Contains only StrEnum classes."""

from enum import StrEnum, auto

__all__ = [
    "Area",
    "Chars",
    "LogName",
    "NavBtn",
    "OperateBtn",
    "OperateHelp",
    "ScreenName",
    "TabBtn",
    "TabName",
    "Tcss",
    "TreeName",
    "ViewName",
]


class Area(StrEnum):
    bottom = auto()
    left = auto()
    right = auto()
    top = auto()


class Chars(StrEnum):
    add_file_info_border = f"local {'\u2014' * 3}\u2192 chezmoi"  # '\N{EM DASH}', '\N{RIGHTWARDS ARROW}'
    apply_file_info_border = f"local \u2190{'\u2014' * 3} chezmoi"  # '\N{LEFTWARDS ARROW}', '\N{EM DASH}'
    bullet = "\u2022"  # '\N{BULLET}'
    burger = "\u2261"  # '\N{IDENTICAL TO}'
    check_mark = "\u2714"  # '\N{HEAVY CHECK MARK}'
    destroy_file_info_border = "\u274c destroy file \u274c"  # '\N{CROSS MARK}'
    down_triangle = "\u25bc "  # '\N{BLACK DOWN-POINTING TRIANGLE}'
    forget_file_info_border = (
        "\u2716 forget file \u2716"  # '\N{HEAVY MULTIPLICATION X}'
    )
    # gear = "\u2699"  # '\N{GEAR}'
    lower_3_8ths_block = "\u2583"  # "\N{LOWER THREE EIGHTHS BLOCK}"
    re_add_file_info_border = f"local {'\u2014' * 3}\u2192 chezmoi"  # '\N{EM DASH}', '\N{RIGHTWARDS ARROW}'
    right_triangle = "\u25b6 "  # '\N{BLACK RIGHT-POINTING TRIANGLE}'
    warning_sign = "\u26a0"  # '\N{WARNING SIGN}'
    x_mark = "\u2716"  # '\N{HEAVY MULTIPLICATION X}'


class LogName(StrEnum):
    app_log = " App Log "
    debug_log = " Debug Log "
    output_log = " Commands With Raw Stdout "


class NavBtn(StrEnum):
    cat_config = "Cat Config"
    clone_repo = "Clone"
    diagram = "Diagram"
    doctor = "Doctor"
    ignored = "Ignored"
    new_repo = "New Repo"
    purge_repo = "Purge Repo"
    template_data = "Template Data"


class OperateBtn(StrEnum):
    add_dir = "Add Dir"
    add_file = "Add File"
    # apply_dir = "Apply Dir"
    apply_file = "Apply File"
    clone_repo = "Clone Existing Repo"
    # destroy_dir = "Destroy Dir"
    destroy_file = "Destroy File"
    # forget_dir = "Forget Dir"
    forget_file = "Forget File"
    new_repo = "Initialize New Repo"
    operate_dismiss = "Cancel"
    purge_repo = "Purge Existing Repo"
    # re_add_dir = "Re-Add Dir"
    re_add_file = "Re-Add File"


class OperateHelp(StrEnum):
    add = "[$text-primary]Path will be added to your chezmoi dotfile manager source state.[/]"
    apply_file = "[$text-primary]The file in the destination directory will be modified.[/]"
    # apply_dir = "[$text-primary]The directory in the destination directory will be modified.[/]"
    auto_commit = f"[$text-warning]{Chars.warning_sign} Auto commit is enabled: files will also be committed.{Chars.warning_sign}[/]"
    autopush = f"[$text-warning]{Chars.warning_sign} Auto push is enabled: files will be pushed to the remote.{Chars.warning_sign}[/]"
    changes_mode_disabled = (
        "Changes mode disabled, operations will dry-run only"
    )
    changes_mode_enabled = "Changes mode enabled, operations will run."
    destroy_file = "[$text-error]Permanently remove the file both from your home directory and chezmoi's source directory, make sure you have a backup![/]"
    # destroy_dir = "[$text-error]Permanently remove the directory both from your home directory and chezmoi's source directory, make sure you have a backup![/]"
    diff_color = "[$text-success]+ green lines will be added[/]\n[$text-error]- red lines will be removed[/]\n[dim]{Chars.bullet} dimmed lines for context[/]"
    forget_file = "[$text-primary]Remove the file from the source state, i.e. stop managing them.[/]"
    # forget_dir = "[$text-primary]Remove the directory from the source state, i.e. stop managing them.[/]"
    re_add_file = (
        "[$text-primary]Overwrite the source state with current local file[/]"
    )
    # re_add_dir = "[$text-primary]Overwrite the source state with thecurrent local directory[/]"


class ScreenName(StrEnum):
    install_help = auto()
    maximized = auto()
    operate = auto()


class TabBtn(StrEnum):
    # Tab buttons for content switcher within a main tab
    app_log = "App"
    contents = "Contents"
    debug_log = "Debug"
    diff = "Diff"
    git_log = "Git-Log"
    list = "List"
    output_log = "Output"
    tree = "Tree"


class TabName(StrEnum):
    add_tab = "Add"
    apply_tab = "Apply"
    config_tab = "Config"
    help_tab = "Help"
    init_tab = "Init"
    logs_tab = "Logs"
    re_add_tab = "Re-Add"


class Tcss(StrEnum):
    border_title_top = auto()
    content_switcher_left = auto()
    dir_tree_widget = auto()
    doctor_listview = auto()
    doctor_table = auto()
    doctor_vertical_scroll = auto()
    flow_diagram = auto()
    input_field = auto()
    input_field_vertical = auto()
    input_select = auto()
    input_select_vertical = auto()
    install_help = auto()
    internet_links = auto()
    last_clicked = auto()
    log_views = auto()
    nav_button = auto()
    nav_content_switcher = auto()
    operate_button = auto()
    operate_info = auto()
    operate_screen = auto()
    pad_bottom = auto()
    screen_base = auto()
    section_label = auto()
    single_button_vertical = auto()
    switch_horizontal = auto()
    switch_label = auto()
    tab_button = auto()
    tab_left_vertical = auto()
    tree_widget = auto()


class TreeName(StrEnum):
    add_tree = auto()
    expanded_tree = auto()
    flat_tree = auto()
    managed_tree = auto()


class ViewName(StrEnum):
    cat_config = auto()
    config_ignored = auto()
    contents_view = auto()
    flow_diagram = auto()
    doctor = auto()
    diff_view = auto()
    git_log_view = auto()
    init_clone_view = auto()
    init_new_view = auto()
    init_purge_view = auto()
    template_data = auto()
