"""Contains subclassed textual classes shared between the AddTab, ApplyTab and
ReAddTab."""

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup
from textual.widgets import Label, Switch

from chezmoi_mousse import Switches, TabName

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["SwitchSlider"]


class SwitchSlider(VerticalGroup):
    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.container.switch_slider)
        if self.ids.tab_name in (TabName.apply, TabName.re_add):
            self.switches = (Switches.unchanged, Switches.expand_all)
        else:  # for the AddTab
            self.switches = (Switches.unmanaged_dirs, Switches.unwanted)

    def compose(self) -> ComposeResult:
        for switch_data in self.switches:
            with HorizontalGroup(
                id=self.ids.switch_horizontal_id(switch=switch_data)
            ):
                yield Switch(id=self.ids.switch_id(switch=switch_data))
                yield Label(switch_data.label).with_tooltip(
                    tooltip=switch_data.enabled_tooltip
                )

    def on_mount(self) -> None:
        self.query(HorizontalGroup).last().styles.padding = 0
