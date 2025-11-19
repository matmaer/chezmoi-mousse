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
    """A canvas is either a TabPane or a Screen."""

    add_tab = auto()
    apply_tab = auto()
    config_tab = auto()
    help_tab = auto()
    init_screen = auto()
    install_help_screen = auto()
    loading_screen = auto()
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
    doctor_table = auto()
    git_log_table = auto()
    git_global_log_table = auto()


class LogName(StrEnum):
    """Names for RichLog widgets."""

    app_logger = auto()
    contents_logger = auto()
    debug_logger = auto()
    diff_logger = auto()
    loading_logger = auto()
    operate_logger = auto()
    read_logger = auto()


class TreeName(StrEnum):
    add_tree = auto()
    expanded_tree = auto()
    list_tree = auto()
    managed_tree = auto()


class ViewName(StrEnum):
    add_help_view = auto()
    apply_help_view = auto()
    cat_config_view = auto()
    contents_view = auto()
    diagram_view = auto()
    doctor_view = auto()
    git_ignored_view = auto()
    git_log_view = auto()
    init_clone_view = auto()
    init_new_view = auto()
    pw_mgr_info_view = auto()
    re_add_help_view = auto()
    template_data_view = auto()
