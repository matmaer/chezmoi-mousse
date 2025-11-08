"""Contains only StrEnum classes with auto() values for naming containers and
widgets.

Used for creating id's, and checking context conditions.
"""

from enum import StrEnum, auto

__all__ = ["CanvasName", "ContainerName", "TreeName", "ViewName"]


class CanvasName(StrEnum):
    """A canvas is either a TabPane, the OperateScreen or the InitScreen."""

    add_tab = auto()
    apply_tab = auto()
    # chezmoi_init = auto() TODO
    config_tab = auto()
    help_tab = auto()
    install_help_screen = auto()
    logs_tab = auto()
    operate_screen = auto()
    reach_out_screen = auto()
    re_add_tab = auto()


class ContainerName(StrEnum):
    config_switcher = auto()
    help_switcher = auto()
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
    # init_new_repo_view = auto() TODO
    pretty_cat_config_view = auto()
    pretty_ignored_view = auto()
    pretty_template_data_view = auto()
    re_add_help_view = auto()
    read_output_log_view = auto()
    template_data_view = auto()
    write_output_log_view = auto()
