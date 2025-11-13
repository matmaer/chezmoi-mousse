from typing import TYPE_CHECKING

from chezmoi_mousse import Switches
from chezmoi_mousse.base.switch_slider import SwitchSliderBase

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds


class SwitchSlider(SwitchSliderBase):
    def __init__(self, *, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(
            ids=self.ids, switches=(Switches.unchanged, Switches.expand_all)
        )
