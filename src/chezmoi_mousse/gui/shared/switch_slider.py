from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup
from textual.widgets import Label, Switch

from chezmoi_mousse import ContainerName, Switches, Tcss

if TYPE_CHECKING:
    from .canvas_ids import CanvasIds

__all__ = ["SwitchSlider"]


class SwitchSlider(VerticalGroup):

    def __init__(
        self, *, ids: "CanvasIds", switches: tuple[Switches, Switches]
    ) -> None:
        self.ids = ids
        self.switch_slider_id = ids.switch_slider_id
        self.switches = switches
        super().__init__(
            id=ids.switch_slider_id(name=ContainerName.switch_slider)
        )

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
        # add padding to the top switch horizontal group
        self.query_one(
            self.ids.switch_horizontal_id("#", switch=self.switches[0]),
            HorizontalGroup,
        ).add_class(Tcss.pad_bottom.name)
