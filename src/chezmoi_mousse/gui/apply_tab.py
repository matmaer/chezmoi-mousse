from typing import TYPE_CHECKING

from textual.app import ComposeResult

from chezmoi_mousse import OperateBtn, Switches

from .shared.button_groups import OperateBtnHorizontal
from .shared.switch_slider import SwitchSlider
from .shared.switchers import TreeSwitcher, ViewSwitcher
from .shared.tabs_base import TabsBase

if TYPE_CHECKING:
    from .shared.canvas_ids import CanvasIds

__all__ = ["ApplyTab"]


class ApplyTab(TabsBase):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(ids=self.ids)

    def compose(self) -> ComposeResult:
        yield TreeSwitcher(self.ids)
        yield ViewSwitcher(ids=self.ids, diff_reverse=False)
        yield OperateBtnHorizontal(
            ids=self.ids,
            buttons=(
                OperateBtn.apply_path,
                OperateBtn.forget_path,
                OperateBtn.destroy_path,
            ),
        )
        yield SwitchSlider(
            ids=self.ids, switches=(Switches.unchanged, Switches.expand_all)
        )
