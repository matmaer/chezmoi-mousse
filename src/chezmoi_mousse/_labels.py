from enum import StrEnum

__all__ = [
    "NavBtn",
    "OperateBtn",
    "OpBtnTooltip",
    "PaneBtn",
    "SwitchLabel",
    "TabBtn",
]


class NavBtn(StrEnum):
    add_help = "Add Help"
    apply_help = "Apply Help"
    cat_config = "Cat Config"
    clone_existing_repo = "Clone Existing Repo"
    diagram = "Diagram"
    doctor = "Doctor"
    exit_app = "Exit App"
    ignored = "Ignored"
    init_new_repo = "Initialize New Repo"
    re_add_help = "Re-Add Help"
    template_data = "Template Data"


class OperateBtn(StrEnum):
    add_dir = "Add Dir"
    add_file = "Add File"
    apply_dir = "Apply Dir"
    apply_file = "Apply File"
    clone_chezmoi_repo = "Clone Repo"
    close_operate_results = "Close Operate Results"
    destroy_dir = "Destroy Dir"
    destroy_file = "Destroy File"
    forget_dir = "Forget Dir"
    forget_file = "Forget File"
    init_new_repo = "Initialize"
    operate_dismiss = "Cancel"
    re_add_dir = "Re-Add Dir"
    re_add_file = "Re-Add File"


class OpBtnTooltip(StrEnum):
    select_file = "Select a file to operate on."
    select_dir = "Select a directory to operate on."
    file_without_status = "The selected file has no status to operate on."
    dir_without_status = "The selected directory has no status to operate on."


class PaneBtn(StrEnum):
    add_tab = "Add"
    apply_tab = "Apply"
    config_tab = "Config"
    destroy_tab = "Destroy"
    forget_tab = "Forget"
    help_tab = "Help"
    logs_tab = "Logs"
    re_add_tab = "Re-Add"


class SwitchLabel(StrEnum):
    expand_all = "expand all dirs"
    unchanged = "show unchanged files"
    unmanaged_dirs = "show unmanaged dirs"
    unwanted = "show unwanted paths"


class TabBtn(StrEnum):
    # Tab buttons for content switcher within a main tab
    app_log = "App Log"
    contents = "Contents"
    debug_log = "Debug Log"
    diff = "Diff"
    git_log_path = "Git Log"
    git_log_global = "Global Git Log"
    list = "List"
    read_output_log = "Read Outputs"
    write_output_log = "Write Outputs"
    tree = "Tree"
