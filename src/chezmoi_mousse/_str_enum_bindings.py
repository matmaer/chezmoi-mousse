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
    toggle_dry_run = "Toggle --dry-run"
    maximize = "Maximize"
    minimize = "Minimize"
