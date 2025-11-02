from enum import StrEnum, auto

__all__ = ["SwitcherName", "FlatBtn", "TabBtn"]


class SwitcherName(StrEnum):
    config_switcher = auto()
    help_switcher = auto()
    logs_switcher = auto()
    tree_switcher = auto()
    view_switcher = auto()


class FlatBtn(StrEnum):
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
