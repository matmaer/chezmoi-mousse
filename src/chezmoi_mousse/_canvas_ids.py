"""Contains classes to enable setting widget id's without hardcoded strings or
generated the id dynamically when subclassing or to query a widget."""

from typing import NamedTuple

from chezmoi_mousse._button_data import FlatBtn, LinkBtn, OperateBtn, TabBtn
from chezmoi_mousse._names import (
    CanvasName,
    ContainerName,
    DataTableName,
    TreeName,
    ViewName,
)
from chezmoi_mousse._switches import Switches

__all__ = ["CanvasIds"]


class ViewsIds(NamedTuple):
    cat_config_btn: str
    cat_config_q: str
    cat_config: str
    doctor_btn: str
    doctor_q: str
    doctor: str
    ignored_btn: str
    ignored_q: str
    ignored: str
    new_repo_btn: str
    new_repo_q: str
    new_repo: str
    pw_mgr_info_btn: str
    pw_mgr_info_q: str
    pw_mgr_info: str
    template_data_btn: str
    template_data_q: str
    template_data: str


class CanvasIds:
    __slots__ = ("canvas_container_id", "canvas_name", "header_id", "views")

    def __init__(self, canvas_name: CanvasName) -> None:
        self.canvas_name: str = canvas_name.name
        self.header_id = f"{self.canvas_name}_header"
        self.canvas_container_id = f"{canvas_name}_container_id"

        self.views = ViewsIds(
            cat_config_btn=self.button_id(btn=FlatBtn.cat_config),
            cat_config_q=self.view_id("#", view=ViewName.cat_config_view),
            cat_config=self.view_id(view=ViewName.cat_config_view),
            doctor_btn=self.button_id(btn=FlatBtn.doctor),
            doctor_q=self.view_id("#", view=ViewName.doctor_view),
            doctor=self.view_id(view=ViewName.doctor_view),
            ignored_btn=self.button_id(btn=FlatBtn.ignored),
            ignored_q=self.view_id("#", view=ViewName.git_ignored_view),
            ignored=self.view_id(view=ViewName.git_ignored_view),
            new_repo_btn=self.button_id(btn=FlatBtn.init_new_repo),
            new_repo_q=self.view_id("#", view=ViewName.init_new_repo_view),
            new_repo=self.view_id(view=ViewName.init_new_repo_view),
            pw_mgr_info_btn=self.button_id(btn=FlatBtn.pw_mgr_info),
            pw_mgr_info_q=self.view_id("#", view=ViewName.pw_mgr_info_view),
            pw_mgr_info=self.view_id(view=ViewName.pw_mgr_info_view),
            template_data_btn=self.button_id(btn=FlatBtn.template_data),
            template_data_q=self.view_id(
                "#", view=ViewName.template_data_view
            ),
            template_data=self.view_id(view=ViewName.template_data_view),
        )

    def button_id(
        self, qid: str = "", *, btn: FlatBtn | LinkBtn | OperateBtn | TabBtn
    ) -> str:
        if isinstance(btn, OperateBtn):
            suffix = "_op_btn"
            return f"{qid}{self.canvas_name}_{btn.name}{suffix}"
        elif isinstance(btn, TabBtn):
            suffix = "_tab_btn"
        elif isinstance(btn, FlatBtn):
            suffix = "_flat_btn"
        else:
            suffix = "_link_btn"
        return f"{qid}{self.canvas_name}_{btn.name}{suffix}"

    def container_id(self, qid: str = "", *, name: ContainerName) -> str:
        return f"{qid}{self.canvas_name}_{name.name}"

    def content_switcher_id(
        self, qid: str = "", *, name: ContainerName
    ) -> str:
        return f"{qid}{self.canvas_name}_{name.name}"

    def datatable_id(
        self, qid: str = "", *, data_table_name: DataTableName
    ) -> str:
        return f"{qid}{self.canvas_name}_{data_table_name.name}_datatable"

    def initial_header_id(self, qid: str = "", *, view_name: ViewName) -> str:
        return f"{qid}{self.canvas_name}_{view_name.name}_initial_header"

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
