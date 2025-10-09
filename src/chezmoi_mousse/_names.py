from enum import StrEnum, auto

# RULES: can only contain auto() members, no assigned values


__all__ = ["LogName", "ScreenName", "SwitchName", "TreeName", "ViewName"]


class AreaName(StrEnum):
    bottom = auto()
    left = auto()
    right = auto()
    top = auto()


class LogName(StrEnum):
    app_log = " App Log "
    debug_log = " Debug Log "
    output_log = " Commands With Raw Stdout "


class ScreenName(StrEnum):
    install_help = auto()
    maximized = auto()
    operate = auto()


class SwitchName(StrEnum):
    expand_all = auto()
    unchanged = auto()
    unmanaged_dirs = auto()
    unwanted = auto()


class TreeName(StrEnum):
    add_tree = auto()
    expanded_tree = auto()
    flat_tree = auto()
    managed_tree = auto()


class ViewName(StrEnum):
    cat_config_view = auto()
    git_ignored_view = auto()
    contents_view = auto()
    diagram_view = auto()
    doctor_view = auto()
    diff_view = auto()
    git_log_view = auto()
    init_clone_view = auto()
    init_new_view = auto()
    init_purge_view = auto()
    template_data_view = auto()
    pretty_cat_config_view = auto()
    pretty_ignored_view = auto()
    pretty_template_data_view = auto()
