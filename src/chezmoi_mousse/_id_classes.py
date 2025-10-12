"""Contains classes to enable setting widget id's without hardcoded strings or
generated the id dynamically when subclassing or to query a widget."""

from dataclasses import dataclass

from chezmoi_mousse._labels import NavBtn, OperateBtn, TabBtn
from chezmoi_mousse._names import AreaName, Canvas, TreeName, ViewName
from chezmoi_mousse._switch_data import SwitchData

__all__ = ["CanvasIds", "Id"]


class CanvasIds:
    def __init__(self, canvas_name: Canvas) -> None:
        self.canvas_name: str = canvas_name.name
        self.tab_container_id = f"{canvas_name}_container_id"
        self.operate_container_id = f"{canvas_name}_operate_container_id"

        # id's for which there's only one widget for each self.canvas_name
        self.datatable_id = f"{canvas_name}_datatable"
        self.datatable_qid = f"#{self.datatable_id}"
        self.listview_id = f"{canvas_name}_listview"
        self.listview_qid = f"#{self.listview_id}"
        self.switches_slider_id = f"{canvas_name}_switches_slider"
        self.switches_slider_qid = f"#{self.switches_slider_id}"

    def button_id(
        self, qid: str = "", *, btn: OperateBtn | TabBtn | NavBtn
    ) -> str:
        if isinstance(btn, OperateBtn):
            suffix = "_op_btn"
        elif isinstance(btn, TabBtn):
            suffix = "_tab_btn"
        else:
            suffix = "_nav_btn"
        return f"{qid}{self.canvas_name}_{btn.name}{suffix}"

    def buttons_horizontal_id(self, area: AreaName) -> str:
        return f"{self.canvas_name}_{area}_horizontal"

    def content_switcher_id(self, qid: str = "", *, area: AreaName) -> str:
        return f"{qid}{self.canvas_name}_{area}_content_switcher"

    def switch_horizontal_id(
        self, qid: str = "", *, switch: SwitchData
    ) -> str:
        return (
            f"{qid}{self.canvas_name}_{switch.switch_name}_switch_horizontal"
        )

    def switch_id(self, qid: str = "", *, switch: SwitchData) -> str:
        return f"{qid}{self.canvas_name}_{switch.switch_name}_switch"

    def tab_vertical_id(self, qid: str = "", *, area: AreaName) -> str:
        return f"{qid}{self.canvas_name}_{area}_vertical"

    def tree_id(self, qid: str = "", *, tree: TreeName) -> str:
        return f"{qid}{self.canvas_name}_{tree}"

    def view_id(self, qid: str = "", *, view: ViewName) -> str:
        return f"{qid}{self.canvas_name}_{view}"


@dataclass(frozen=True)
class Id:
    add_tab: CanvasIds = CanvasIds(Canvas.add)
    apply_tab: CanvasIds = CanvasIds(Canvas.apply)
    config_tab: CanvasIds = CanvasIds(Canvas.config)
    help_tab: CanvasIds = CanvasIds(Canvas.help)
    logs_tab: CanvasIds = CanvasIds(Canvas.logs)
    re_add_tab: CanvasIds = CanvasIds(Canvas.re_add)
    init_screen: CanvasIds = CanvasIds(Canvas.init)
    maximized_layer: CanvasIds = CanvasIds(Canvas.maximized)
    operate_layer: CanvasIds = CanvasIds(Canvas.operate)
