from enum import StrEnum, auto

__all__ = [
    "BindingAction",
    "ContainerName",
    "LabelName",
    "LogName",
    "ScreenName",
    "StaticName",
    "Tcss",
    "TreeName",
    "ViewName",
]


class BindingAction(StrEnum):
    toggle_dry_run = auto()
    toggle_maximized = auto()
    toggle_switch_slider = auto()


class ContainerName(StrEnum):
    command_output = auto()
    contents = auto()
    diff = auto()
    dir_contents = auto()
    doctor = auto()
    file_contents = auto()
    git_log = auto()
    left_side = auto()
    op_cmd_results = auto()
    op_mode = auto()
    operate_buttons = auto()
    repo_input = auto()
    right_side = auto()


class LabelName(StrEnum):
    cat_config_output = auto()
    loading = auto()


class LogName(StrEnum):
    app_logger = auto()
    cmd_logger = auto()
    debug_logger = auto()
    dom_node_logger = auto()
    memory_usage_logger = auto()


class ScreenName(StrEnum):
    init = auto()
    install_help = auto()
    main_tabs = auto()
    splash = auto()


class StaticName(StrEnum):
    debug_test_paths = auto()
    init_info = auto()
    operate_info = auto()


class Tcss(StrEnum):
    added = auto()
    changed = auto()
    changes_enabled_color = auto()
    context = auto()
    debug_content_switcher = auto()
    flat_button = auto()
    flat_section_label = auto()
    flow_diagram = auto()
    guess_link = auto()
    info = auto()
    input_field = auto()
    input_select = auto()
    last_clicked_flat_btn = auto()
    last_clicked_tab_btn = auto()
    main_section_label = auto()
    operate_button = auto()
    operate_info = auto()
    pw_mgr_group = auto()
    refresh_button = auto()
    removed = auto()
    single_button_vertical = auto()
    sub_section_label = auto()
    tab_button = auto()
    tab_left_vertical = auto()
    tree_content_switcher = auto()
    tree_widget = auto()
    unhandled = auto()

    # add a property to return the name with a dot prefix
    @property
    def dot_prefix(self) -> str:
        return f".{self.value}"


class TreeName(StrEnum):
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
