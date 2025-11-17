"""Contains only StrEnum classes with auto() values for naming containers and
widgets.

Used for creating id's, and checking context conditions.
"""

from enum import StrEnum, auto

__all__ = [
    "CanvasName",
    "ContainerName",
    "DataTableName",
    "LogName",
    "TreeName",
    "ViewName",
]


class CanvasName(StrEnum):
    """A canvas is either a TabPane, the OperateScreen or the InitScreen."""

    add_tab = auto()
    apply_tab = auto()
    # chezmoi_init = auto() TODO
    config_tab = auto()
    help_tab = auto()
    init_screen = auto()
    install_help_screen = auto()
    logs_tab = auto()
    main_screen = auto()
    operate_screen = auto()
    re_add_tab = auto()


class ContainerName(StrEnum):
    config_switcher = auto()
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
    git_log_table = auto()
    doctor_table = auto()


class LogName(StrEnum):
    init_clone_repo = auto()
    init_new_repo = auto()
    logs_tab_app = auto()
    logs_tab_debug = auto()
    logs_tab_git = auto()
    logs_tab_operate = auto()
    logs_tab_read = auto()
    operate_screen = auto()
    view_tabs_git = auto()


class TreeName(StrEnum):
    add_tree = auto()
    expanded_tree = auto()
    list_tree = auto()
    managed_tree = auto()


class ViewName(StrEnum):
    add_help_view = auto()
    app_log_view = auto()
    apply_help_view = auto()
    cat_config_view = auto()
    # clone_existing_repo_view = auto() TODO
    contents_view = auto()
    debug_log_view = auto()
    diagram_view = auto()
    diff_view = auto()
    doctor_view = auto()
    git_ignored_view = auto()
    git_log_view = auto()
    init_new_repo_view = auto()
    pw_mgr_info_view = auto()
    re_add_help_view = auto()
    read_log_view = auto()
    template_data_view = auto()
    operate_log_view = auto()
