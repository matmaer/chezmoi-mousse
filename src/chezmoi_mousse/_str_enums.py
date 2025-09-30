"""Contains only StrEnum classes."""

from enum import StrEnum, auto


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
    re_add = f"local {'\u2014' * 3}\u2192 chezmoi"  # '\N{EM DASH}', '\N{RIGHTWARDS ARROW}'
    re_add_file_info_border = f"local {'\u2014' * 3}\u2192 chezmoi"  # '\N{EM DASH}', '\N{RIGHTWARDS ARROW}'
    right_triangle = "\u25b6 "  # '\N{BLACK RIGHT-POINTING TRIANGLE}'
    warning_sign = "\u26a0"  # '\N{WARNING SIGN}'
    x_mark = "\u2716"  # '\N{HEAVY MULTIPLICATION X}'


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
    add_tab = auto()
    apply_tab = auto()
    config_tab = auto()
    help_tab = auto()
    init_tab = auto()
    log_tab = auto()
    re_add_tab = auto()


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
