from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup
from textual.widgets import Label, Switch

from chezmoi_mousse import Switches, Tcss

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds


__all__ = ["SwitchSlider"]


class SwitchSlider(VerticalGroup):

    def __init__(
        self, *, ids: "CanvasIds", switches: tuple[Switches, Switches]
    ) -> None:
        self.switches = switches
        self.ids = ids
        super().__init__(id=self.ids.switches_slider_id)

    def compose(self) -> ComposeResult:
        for switch_data in self.switches:
            with HorizontalGroup(
                id=self.ids.switch_horizontal_id(switch=switch_data.value),
                classes=Tcss.switch_horizontal.name,
            ):
                yield Switch(id=self.ids.switch_id(switch=switch_data.value))
                yield Label(
                    switch_data.value.label, classes=Tcss.switch_label.name
                ).with_tooltip(tooltip=switch_data.value.tooltip)

    def on_mount(self) -> None:
        # add padding to the top switch horizontal group
        self.query_one(
            self.ids.switch_horizontal_id("#", switch=self.switches[0].value),
            HorizontalGroup,
        ).add_class(Tcss.pad_bottom.name)
