from enum import StrEnum, auto

__all__ = [
    "BindingAction",
    "ContainerName",
    "LogName",
    "ScreenName",
    "StaticName",
    "Tcss",
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
    doctor = auto()
    git_log = auto()
    left_side = auto()
    op_feed_back = auto()
    operate_buttons = auto()
    repo_input = auto()
    right_side = auto()


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
    changed_paths = auto()
    debug_test_paths = auto()
    init_info = auto()
    operate_info = auto()


class Tcss(StrEnum):
    added = auto()
    changed = auto()
    changes_enabled_color = auto()
    context = auto()
    dest_dir_tree_label = auto()
    flat_button = auto()
    flat_section_label = auto()
    flow_diagram = auto()
    full_cmd = auto()
    info = auto()
    init_docs_link = auto()
    input_field = auto()
    input_select = auto()
    last_clicked_flat_btn = auto()
    last_clicked_tab_btn = auto()
    limited_label = auto()
    main_section_label = auto()
    operate_button = auto()
    operate_info = auto()
    pw_mgr_group = auto()
    refresh_button = auto()
    removed = auto()
    single_button_vertical = auto()
    single_switch = auto()
    sub_section_label = auto()
    tab_button = auto()
    tab_left_vertical = auto()
    tree_widget = auto()
    tree_widgets = auto()
    unhandled = auto()

    # add a property to return the name with a dot prefix
    @property
    def dot_prefix(self) -> str:
        return f".{self.value}"


class ViewName(StrEnum):
    add_help_view = auto()
    apply_help_view = auto()
    cat_config_view = auto()
    debug_log_view = auto()
    diagram_view = auto()
    dom_nodes_view = auto()
    git_ignored_view = auto()
    memory_usage_view = auto()
    pw_mgr_info_view = auto()
    re_add_help_view = auto()
    template_data_view = auto()
    test_paths_view = auto()
