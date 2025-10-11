from enum import StrEnum

__all__ = ["NavBtn", "OperateBtn", "PaneBtn", "SwitchLabel", "TabBtn"]


class NavBtn(StrEnum):
    cat_config = "Cat Config"
    clone_repo = "Clone"
    diagram = "Diagram"
    doctor = "Doctor"
    ignored = "Ignored"
    new_repo = "New Repo"
    purge_repo = "Purge Repo"
    template_data = "Template Data"


class OperateBtn(StrEnum):
    add_dir = "Add Dir"
    add_file = "Add File"
    # apply_dir = "Apply Dir"
    apply_file = "Apply File"
    clone_repo = "Clone Existing Repo"
    # destroy_dir = "Destroy Dir"
    destroy_file = "Destroy File"
    # forget_dir = "Forget Dir"
    forget_file = "Forget File"
    new_repo = "Initialize New Repo"
    operate_dismiss = "Cancel"
    purge_repo = "Purge Existing Repo"
    # re_add_dir = "Re-Add Dir"
    re_add_file = "Re-Add File"


class PaneBtn(StrEnum):
    add_tab = "Add"
    apply_tab = "Apply"
    config_tab = "Config"
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
    app_log = "App"
    contents = "Contents"
    debug_log = "Debug"
    diff = "Diff"
    git_log = "Git-Log"
    list = "List"
    output_log = "Output"
    tree = "Tree"
