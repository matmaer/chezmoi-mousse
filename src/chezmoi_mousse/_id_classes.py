"""Contains classes to enable setting widget id's without hardcoded strings or
generated the id dynamically when subclassing or to query a widget."""

from typing import ClassVar

from chezmoi_mousse._labels import NavBtn, TabBtn
from chezmoi_mousse._names import AreaName, Canvas, TreeName, ViewName
from chezmoi_mousse._operate_buttons import OperateBtn
from chezmoi_mousse._switches import Switches

__all__ = ["CanvasIds", "Id"]


class CanvasIds:
    __slots__ = (
        "canvas_name",
        "tab_container_id",
        "tab_container_qid",
        "datatable_id",
        "listview_id",
        "switches_slider_id",
        "switches_slider_qid",
    )

    def __init__(self, canvas_name: Canvas) -> None:
        self.canvas_name: str = canvas_name.name

        # id's for which there's only one widget for each self.canvas_name
        self.datatable_id = f"{canvas_name}_datatable"
        self.listview_id = f"{canvas_name}_listview"
        self.switches_slider_id = f"{canvas_name}_switches_slider"
        self.switches_slider_qid = f"#{self.switches_slider_id}"
        self.tab_container_id = f"{canvas_name}_container_id"
        self.tab_container_qid = f"#{self.tab_container_id}"

    def button_id(
        self, qid: str = "", *, btn: OperateBtn | TabBtn | NavBtn
    ) -> str:
        if isinstance(btn, OperateBtn):
            suffix = "_op_btn"
            return f"{qid}{self.canvas_name}_{btn.name}{suffix}"
        elif isinstance(btn, TabBtn):
            suffix = "_tab_btn"
        else:
            suffix = "_nav_btn"
        return f"{qid}{self.canvas_name}_{btn.name}{suffix}"

    def buttons_horizontal_id(self, qid: str = "", *, area: AreaName) -> str:
        return f"{qid}{self.canvas_name}_{area}_button_group"

    def content_switcher_id(self, qid: str = "", *, area: AreaName) -> str:
        return f"{qid}{self.canvas_name}_{area}_content_switcher"

    def switch_horizontal_id(self, qid: str = "", *, switch: Switches) -> str:
        return f"{qid}{self.canvas_name}_{switch.value.switch_name}_switch_horizontal"

    def switch_id(self, qid: str = "", *, switch: Switches) -> str:
        return f"{qid}{self.canvas_name}_{switch.value.switch_name}_switch"

    def tab_vertical_id(self, qid: str = "", *, area: AreaName) -> str:
        return f"{qid}{self.canvas_name}_{area}_vertical"

    def tree_id(self, qid: str = "", *, tree: TreeName) -> str:
        return f"{qid}{self.canvas_name}_{tree}"

    def view_id(self, qid: str = "", *, view: ViewName) -> str:
        return f"{qid}{self.canvas_name}_{view}"


class Id:
    add_tab: ClassVar[CanvasIds] = CanvasIds(Canvas.add)
    apply_tab: ClassVar[CanvasIds] = CanvasIds(Canvas.apply)
    chezmoi_init: ClassVar[CanvasIds] = CanvasIds(Canvas.chezmoi_init)
    config_tab: ClassVar[CanvasIds] = CanvasIds(Canvas.config)
    help_tab: ClassVar[CanvasIds] = CanvasIds(Canvas.help)
    logs_tab: ClassVar[CanvasIds] = CanvasIds(Canvas.logs)
    operate_launch: ClassVar[CanvasIds] = CanvasIds(Canvas.operate_launch)
    operate_result: ClassVar[CanvasIds] = CanvasIds(Canvas.operate_result)
    re_add_tab: ClassVar[CanvasIds] = CanvasIds(Canvas.re_add)
