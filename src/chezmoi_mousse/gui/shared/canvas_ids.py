"""Contains classes to enable setting widget id's without hardcoded strings or
generated the id dynamically when subclassing or to query a widget."""

from chezmoi_mousse import (
    CanvasName,
    ContainerName,
    FlatBtn,
    OperateBtn,
    Switches,
    TabBtn,
    TreeName,
    ViewName,
)

__all__ = ["CanvasIds"]


class CanvasIds:
    __slots__ = (
        "canvas_name",
        "datatable_id",
        "datatable_qid",
        "listview_id",
        "tab_container_id",
    )

    def __init__(self, canvas_name: CanvasName) -> None:
        self.canvas_name: str = canvas_name.name
        self.datatable_id = f"{canvas_name}_datatable"
        self.datatable_qid = f"#{canvas_name}_datatable"
        self.listview_id = f"{canvas_name}_listview"
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

    def buttons_group_id(self, qid: str = "", *, name: ContainerName) -> str:
        return f"{qid}{self.canvas_name}_{name.name}"

    def content_switcher_id(
        self, qid: str = "", *, name: ContainerName
    ) -> str:
        return f"{qid}{self.canvas_name}_{name.name}"

    def switch_slider_id(self, qid: str = "", *, name: ContainerName) -> str:
        return f"{qid}{self.canvas_name}_{name.name}"

    def switch_horizontal_id(self, qid: str = "", *, switch: Switches) -> str:
        return (
            f"{qid}{self.canvas_name}_{switch.switch_name}_switch_horizontal"
        )

    def switch_id(self, qid: str = "", *, switch: Switches) -> str:
        return f"{qid}{self.canvas_name}_{switch.switch_name}_switch"

    def tab_vertical_id(self, qid: str = "", *, name: ContainerName) -> str:
        return f"{qid}{self.canvas_name}_{name.name}_vertical"

    def tree_id(self, qid: str = "", *, tree: TreeName) -> str:
        return f"{qid}{self.canvas_name}_{tree}"

    def view_id(self, qid: str = "", *, view: ViewName) -> str:
        return f"{qid}{self.canvas_name}_{view}"
