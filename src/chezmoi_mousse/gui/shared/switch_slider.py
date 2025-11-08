from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup
from textual.widgets import Label, Switch

from chezmoi_mousse import ContainerName, Switches, Tcss

if TYPE_CHECKING:
    from .canvas_ids import CanvasIds

__all__ = ["AddSwitchSlider", "ApplySwitchSlider", "ReAddSwitchSlider"]


class SwitchSliderBase(VerticalGroup):

    def __init__(
        self, *, ids: "CanvasIds", switches: tuple[Switches, ...]
    ) -> None:
        self.ids = ids
        self.switches = switches
        super().__init__(
            id=ids.container_id(name=ContainerName.switch_slider),
            classes=Tcss.switch_slider.name,
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
        switch_groups = self.query_children(HorizontalGroup)
        switch_groups[-1].styles.padding = 0


class AddSwitchSlider(SwitchSliderBase):
    def __init__(self, *, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(
            ids=self.ids, switches=(Switches.unmanaged_dirs, Switches.unwanted)
        )


class ApplySwitchSlider(SwitchSliderBase):
    def __init__(self, *, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(
            ids=self.ids, switches=(Switches.unchanged, Switches.expand_all)
        )


class ReAddSwitchSlider(SwitchSliderBase):
    def __init__(self, *, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(
            ids=self.ids, switches=(Switches.unchanged, Switches.expand_all)
        )
