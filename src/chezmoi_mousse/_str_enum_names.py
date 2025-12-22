from enum import StrEnum, auto

__all__ = [
    "ContainerName",
    "ContentSwitcherName",
    "DataTableName",
    "LabelName",
    "LogName",
    "PathKind",
    "ScreenName",
    "StaticName",
    "TabName",
    "TreeName",
    "ViewName",
]


class ContainerName(StrEnum):
    contents = auto()
    contents_info = auto()
    diff = auto()
    diff_info = auto()
    diff_lines = auto()
    diff_output = auto()
    doctor = auto()
    git_log_global = auto()
    git_log_path = auto()
    left_side = auto()
    operate_buttons = auto()
    post_operate = auto()
    pre_operate = auto()
    repo_input = auto()
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


class LabelName(StrEnum):
    cat_config_output = auto()
    contents_info = auto()
    diff_cmd = auto()
    file_read_output = auto()


class LogName(StrEnum):
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
    install_help = auto()
    main_tabs = auto()
    operate_init = auto()
    operate_chezmoi = auto()
    splash = auto()


class StaticName(StrEnum):
    contents_info = auto()
    diff_info = auto()
    diff_lines = auto()
    git_log_info = auto()
    init_info = auto()
    operate_info = auto()
    operate_output = auto()


class TabName(StrEnum):
    add = auto()
    apply = auto()
    config = auto()
    help = auto()
    logs = auto()
    re_add = auto()


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
    pw_mgr_info_view = auto()
    re_add_help_view = auto()
    template_data_view = auto()
