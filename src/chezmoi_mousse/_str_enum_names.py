from enum import StrEnum, auto

__all__ = [
    "BindingAction",
    "ContainerName",
    "ContentSwitcherName",
    "DataTableName",
    "LabelName",
    "LogName",
    "PathKind",
    "ScreenName",
    "StaticName",
    "TabName",
    "Tcss",
    "TreeName",
    "ViewName",
]


class BindingAction(StrEnum):
    exit_screen = auto()
    toggle_dry_run = auto()
    toggle_maximized = auto()
    toggle_switch_slider_visibility = auto()


class ContainerName(StrEnum):
    command_output = auto()
    contents = auto()
    contents_info = auto()
    diff = auto()
    doctor = auto()
    git_log_global = auto()
    git_log_path = auto()
    left_side = auto()
    op_mode = auto()
    op_result = auto()
    op_review = auto()
    operate_buttons = auto()
    repo_input = auto()
    right_side = auto()
    switch_slider = auto()


class ContentSwitcherName(StrEnum):
    apply_tree_switcher = auto()
    apply_view_switcher = auto()
    config_switcher = auto()
    debug_switcher = auto()
    help_switcher = auto()
    init_screen_switcher = auto()
    logs_switcher = auto()
    re_add_tree_switcher = auto()
    re_add_view_switcher = auto()


class DataTableName(StrEnum):
    doctor_table = auto()
    git_log_table = auto()


class LabelName(StrEnum):
    cat_config_output = auto()
    contents_info = auto()
    file_read_output = auto()


class LogName(StrEnum):
    app_logger = auto()
    contents_logger = auto()
    debug_logger = auto()
    dom_node_logger = auto()
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
    init = auto()
    splash = auto()


class StaticName(StrEnum):
    contents_info = auto()
    debug_test_paths = auto()
    diff_info = auto()
    diff_lines = auto()
    git_log_info = auto()
    init_info = auto()
    op_result_info = auto()
    op_review_info = auto()


class TabName(StrEnum):
    add = auto()
    apply = auto()
    config = auto()
    debug = auto()
    help = auto()
    logs = auto()
    re_add = auto()


class Tcss(StrEnum):
    added = auto()
    border_title_top = auto()
    changed = auto()
    changes_enabled_color = auto()
    cmd_output = auto()
    content_switcher_left = auto()
    context = auto()
    doctor_table = auto()
    flat_button = auto()
    flat_section_label = auto()
    flow_diagram = auto()
    guess_link = auto()
    input_field = auto()
    input_select = auto()
    last_clicked_flat_btn = auto()
    last_clicked_tab_btn = auto()
    main_section_label = auto()
    operate_button = auto()
    operate_button_group = auto()
    operate_info = auto()
    pw_mgr_group = auto()
    removed = auto()
    single_button_vertical = auto()
    single_switch = auto()
    sub_section_label = auto()
    tab_button = auto()
    tab_left_vertical = auto()
    tree_widget = auto()
    unchanged = auto()

    # add a property to return the name with a dot prefix
    @property
    def dot_prefix(self) -> str:
        return f".{self.value}"


class TreeName(StrEnum):
    dir_tree = auto()
    expanded_tree = auto()
    list_tree = auto()
    managed_tree = auto()


class ViewName(StrEnum):
    add_help_view = auto()
    apply_help_view = auto()
    cat_config_view = auto()
    debug_log_view = auto()
    debug_test_paths_view = auto()
    diagram_view = auto()
    git_ignored_view = auto()
    pw_mgr_info_view = auto()
    re_add_help_view = auto()
    template_data_view = auto()
