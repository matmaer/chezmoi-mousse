from enum import StrEnum, auto

__all__ = ["AreaName", "Canvas", "TreeName", "ViewName"]


class AreaName(StrEnum):
    bottom = auto()
    left = auto()
    right = auto()
    top = auto()


class Canvas(StrEnum):
    """A canvas is either a TabPane, the OperateScreen or the InitScreen."""

    add = auto()
    apply = auto()
    # chezmoi_init = auto() TODO
    config = auto()
    help = auto()
    install_help = auto()
    logs = auto()
    operate = auto()
    re_add = auto()


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
