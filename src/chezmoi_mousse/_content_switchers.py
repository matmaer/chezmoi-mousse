from enum import StrEnum

__all__ = ["NavBtn", "TabBtn"]


class OperateButtons(StrEnum):
    add_dir = "Add Dir"
    add_file = "Add File"
    apply_dir = "Apply Dir"
    apply_file = "Apply File"
    apply_path = "Apply Path"
    destroy_dir = "Destroy Dir"
    destroy_file = "Destroy File"
    destroy_path = "Destroy Path"
    forget_dir = "Forget Dir"
    forget_file = "Forget File"
    forget_path = "Forget Path"
    operate_cancel = "Cancel"
    operate_close = "Close"
    re_add_dir = "Re-Add Dir"
    re_add_file = "Re-Add File"
    re_add_path = "Re-Add Path"


class NavBtn(StrEnum):
    add_help = "Add Help"
    apply_help = "Apply Help"
    cat_config = "Cat Config"
    # clone_existing_repo = "Clone Existing Repo" TODO
    diagram = "Diagram"
    doctor = "Doctor"
    exit_app = "Exit App"
    ignored = "Ignored"
    # init_new_repo = "Initialize New Repo" TODO
    re_add_help = "Re-Add Help"
    template_data = "Template Data"


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
