from enum import StrEnum

__all__ = [
    "NavBtn",
    "OperateBtn",
    "PaneBtn",
    "SubTitles",
    "SwitchLabel",
    "TabBtn",
]


class NavBtn(StrEnum):
    add_help = "Add Help"
    apply_help = "Apply Help"
    cat_config = "Cat Config"
    diagram = "Diagram"
    doctor = "Doctor"
    ignored = "Ignored"
    re_add_help = "Re-Add Help"
    template_data = "Template Data"


class OperateBtn(StrEnum):
    add_dir = "Add Dir"
    add_file = "Add File"
    apply_file = "Apply File"
    close_operate_results = "Close Operate Results"
    destroy_file = "Destroy File"
    forget_file = "Forget File"
    operate_dismiss = "Cancel"
    re_add_file = "Re-Add File"


class PaneBtn(StrEnum):
    add_tab = "Add"
    apply_tab = "Apply"
    config_tab = "Config"
    help_tab = "Help"
    logs_tab = "Logs"
    re_add_tab = "Re-Add"


class SubTitles(StrEnum):
    double_click_or_esc = " double click or escape key to close "
    escape = " escape key to close "
    escape_exit_app = " escape key to exit app "


class SwitchLabel(StrEnum):
    expand_all = "expand all dirs"
    unchanged = "show unchanged files"
    unmanaged_dirs = "show unmanaged dirs"
    unwanted = "show unwanted paths"


class TabBtn(StrEnum):
    # Tab buttons for content switcher within a main tab
    app_log = "App"
    contents = "Contents"
    debug_log = "Debug"
    diff = "Diff"
    git_log = "Git-Log"
    list = "List"
    output_log = "Output"
    tree = "Tree"
