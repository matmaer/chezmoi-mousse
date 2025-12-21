from enum import StrEnum, auto

from ._operate_button_data import OpBtnLabels

__all__ = ["BindingAction", "BindingDescription"]


class BindingAction(StrEnum):
    exit_screen = auto()
    toggle_dry_run = auto()
    toggle_maximized = auto()
    toggle_switch_slider = auto()


class BindingDescription(StrEnum):
    # Screen bindings
    cancel = OpBtnLabels.cancel
    reload = OpBtnLabels.reload
    # Tab bindings
    hide_filters = "Hide filters"
    show_filters = "Show filters"
    # Shared bindings
    toggle_dry_run = "Toggle --dry-run"
    maximize = "Maximize"
    minimize = "Minimize"
