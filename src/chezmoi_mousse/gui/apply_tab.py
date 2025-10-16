from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Vertical

from chezmoi_mousse import AreaName, Switches, TabBtn, Tcss

from .shared._event_hub import EventHub
from .shared.button_groups import TabBtnHorizontal
from .shared.operate.contents_and_diff import TreeSwitcher, ViewSwitcher
from .shared.switch_slider import SwitchSlider

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["ApplyTab"]


class ApplyTab(EventHub):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(ids=self.ids)

    def compose(self) -> ComposeResult:
        with Vertical(
            id=self.ids.tab_vertical_id(area=AreaName.left),
            classes=Tcss.tab_left_vertical.name,
        ):
            yield TabBtnHorizontal(
                ids=self.ids,
                buttons=(TabBtn.tree, TabBtn.list),
                area=AreaName.left,
            )
            yield TreeSwitcher(self.ids)
        with Vertical(id=self.ids.tab_vertical_id(area=AreaName.right)):
            yield TabBtnHorizontal(
                ids=self.ids,
                buttons=(TabBtn.diff, TabBtn.contents, TabBtn.git_log),
                area=AreaName.right,
            )
            yield ViewSwitcher(ids=self.ids, diff_reverse=False)
        yield SwitchSlider(
            ids=self.ids, switches=(Switches.unchanged, Switches.expand_all)
        )
