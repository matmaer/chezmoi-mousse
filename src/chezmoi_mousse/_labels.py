from enum import StrEnum

__all__ = ["NavBtn", "PaneBtn", "TabBtn"]


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


class PaneBtn(StrEnum):
    add_tab = "Add"
    apply_tab = "Apply"
    config_tab = "Config"
    destroy_tab = "Destroy"
    forget_tab = "Forget"
    help_tab = "Help"
    logs_tab = "Logs"
    re_add_tab = "Re-Add"


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
