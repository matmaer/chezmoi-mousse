from enum import StrEnum, auto

__all__ = ["BindingAction", "BindingDescription"]


class BindingAction(StrEnum):
    exit_screen = auto()
    toggle_dry_run = auto()
    toggle_maximized = auto()
    toggle_switch_slider = auto()


class BindingDescription(StrEnum):
    # Screen bindings
    cancel = "Cancel"
    reload = "Close & Reload"
    # Tab bindings
    hide_filters = "Hide filters"
    show_filters = "Show filters"
    # Shared bindings
    add_dry_run_flag = "Add --dry-run flag"
    maximize = "Maximize"
    minimize = "Minimize"
    remove_dry_run_flag = "Remove --dry-run flag"
