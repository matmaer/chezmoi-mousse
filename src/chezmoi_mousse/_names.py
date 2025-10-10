from enum import StrEnum, auto

# RULES: can only contain auto() members, no assigned values


__all__ = ["ScreenName", "TreeName", "ViewName"]


class AreaName(StrEnum):
    bottom = auto()
    left = auto()
    right = auto()
    top = auto()


class ScreenName(StrEnum):
    install_help = auto()
    maximized = auto()
    operate = auto()


class TreeName(StrEnum):
    add_tree = auto()
    expanded_tree = auto()
    flat_tree = auto()
    managed_tree = auto()


class ViewName(StrEnum):
    app_log_view = auto()
    cat_config_view = auto()
    contents_view = auto()
    debug_log_view = auto()
    diagram_view = auto()
    diff_view = auto()
    doctor_view = auto()
    git_ignored_view = auto()
    git_log_view = auto()
    init_clone_view = auto()
    init_new_view = auto()
    init_purge_view = auto()
    output_log_view = auto()
    pretty_cat_config_view = auto()
    pretty_ignored_view = auto()
    pretty_template_data_view = auto()
    template_data_view = auto()
