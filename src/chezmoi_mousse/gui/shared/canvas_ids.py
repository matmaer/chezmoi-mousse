"""Contains classes to enable setting widget id's without hardcoded strings or
generated the id dynamically when subclassing or to query a widget."""

from chezmoi_mousse import (
    AreaName,
    ButtonGroupName,
    CanvasName,
    FlatBtn,
    OperateBtn,
    SwitcherName,
    Switches,
    TabBtn,
    TreeName,
    ViewName,
)

__all__ = ["CanvasIds"]


class CanvasIds:
    __slots__ = (
        "canvas_name",
        "tab_container_id",
        "datatable_id",
        "listview_id",
        "switches_slider_id",
        "switches_slider_qid",
    )

    def __init__(self, canvas_name: CanvasName) -> None:
        self.canvas_name: str = canvas_name.name

        # id's for which there's only one widget for each self.canvas_name
        self.datatable_id = f"{canvas_name}_datatable"
        self.listview_id = f"{canvas_name}_listview"
        self.switches_slider_id = f"{canvas_name}_switches_slider"
        self.switches_slider_qid = f"#{self.switches_slider_id}"
        self.tab_container_id = f"{canvas_name}_container_id"

    def button_id(
        self, qid: str = "", *, btn: OperateBtn | TabBtn | FlatBtn
    ) -> str:
        if isinstance(btn, OperateBtn):
            suffix = "_op_btn"
            return f"{qid}{self.canvas_name}_{btn.name}{suffix}"
        elif isinstance(btn, TabBtn):
            suffix = "_tab_btn"
        else:
            suffix = "_nav_btn"
        return f"{qid}{self.canvas_name}_{btn.name}{suffix}"

    def buttons_group_id(
        self, qid: str = "", *, group_name: ButtonGroupName
    ) -> str:
        return f"{qid}{self.canvas_name}_{group_name}"

    def content_switcher_id(
        self, qid: str = "", *, switcher_name: SwitcherName
    ) -> str:
        return f"{qid}{self.canvas_name}_{switcher_name.name}"

    def switch_horizontal_id(self, qid: str = "", *, switch: Switches) -> str:
        return (
            f"{qid}{self.canvas_name}_{switch.switch_name}_switch_horizontal"
        )

    def switch_id(self, qid: str = "", *, switch: Switches) -> str:
        return f"{qid}{self.canvas_name}_{switch.switch_name}_switch"

    def tab_vertical_id(self, qid: str = "", *, area: AreaName) -> str:
        return f"{qid}{self.canvas_name}_{area}_vertical"

    def tree_id(self, qid: str = "", *, tree: TreeName) -> str:
        return f"{qid}{self.canvas_name}_{tree}"

    def view_id(self, qid: str = "", *, view: ViewName) -> str:
        return f"{qid}{self.canvas_name}_{view}"
