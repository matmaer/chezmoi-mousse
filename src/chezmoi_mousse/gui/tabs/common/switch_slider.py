"""Contains subclassed textual classes shared between the ApplyTab and
ReAddTab."""

from typing import TYPE_CHECKING

from chezmoi_mousse import Switches
from chezmoi_mousse.shared import SwitchSliderBase

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["SwitchSlider"]


class SwitchSlider(SwitchSliderBase):
    def __init__(self, *, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(
            ids=self.ids, switches=(Switches.unchanged, Switches.expand_all)
        )
