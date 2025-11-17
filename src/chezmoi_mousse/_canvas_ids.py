"""Contains classes to enable setting widget id's without hardcoded strings.

Easy access, autocomplete, type checking or to generated the id dynamically.
"""

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


class ViewIds:
    def __init__(self, canvas_ids: "CanvasIds"):
        # Pre-compute for easy access, auto-completion and see type errors.
        self.add_help_btn = canvas_ids.button_id(btn=FlatBtn.add_help)
        self.add_help = canvas_ids.view_id(view=ViewName.add_help_view)
        self.add_help_q = f"#{self.add_help}"
        self.apply_help_btn = canvas_ids.button_id(btn=FlatBtn.apply_help)
        self.apply_help = canvas_ids.view_id(view=ViewName.apply_help_view)
        self.apply_help_q = f"#{self.apply_help}"
        self.cat_config_btn = canvas_ids.button_id(btn=FlatBtn.cat_config)
        self.cat_config = canvas_ids.view_id(view=ViewName.cat_config_view)
        self.cat_config_q = f"#{self.cat_config}"
        self.diagram_btn = canvas_ids.button_id(btn=FlatBtn.diagram)
        self.diagram = canvas_ids.view_id(view=ViewName.diagram_view)
        self.diagram_q = f"#{self.diagram}"
        self.doctor_btn = canvas_ids.button_id(btn=FlatBtn.doctor)
        self.doctor = canvas_ids.view_id(view=ViewName.doctor_view)
        self.doctor_q = f"#{self.doctor}"
        self.ignored_btn = canvas_ids.button_id(btn=FlatBtn.ignored)
        self.ignored = canvas_ids.view_id(view=ViewName.git_ignored_view)
        self.ignored_q = f"#{self.ignored}"
        self.new_repo_btn = canvas_ids.button_id(btn=FlatBtn.init_new_repo)
        self.new_repo = canvas_ids.view_id(view=ViewName.init_new_repo_view)
        self.new_repo_q = f"#{self.new_repo}"
        self.pw_mgr_info_btn = canvas_ids.button_id(btn=FlatBtn.pw_mgr_info)
        self.pw_mgr_info = canvas_ids.view_id(view=ViewName.pw_mgr_info_view)
        self.pw_mgr_info_q = f"#{self.pw_mgr_info}"
        self.re_add_help_btn = canvas_ids.button_id(btn=FlatBtn.re_add_help)
        self.re_add_help = canvas_ids.view_id(view=ViewName.re_add_help_view)
        self.re_add_help_q = f"#{self.re_add_help}"
        self.template_data_btn = canvas_ids.button_id(
            btn=FlatBtn.template_data
        )
        self.template_data = canvas_ids.view_id(
            view=ViewName.template_data_view
        )
        self.template_data_q = f"#{self.template_data}"


class CanvasIds:
    __slots__ = ("canvas_container_id", "canvas_name", "header_id", "views")

    def __init__(self, canvas_name: CanvasName) -> None:
        self.canvas_name: str = canvas_name.name
        self.header_id = f"{self.canvas_name}_header"
        self.canvas_container_id = f"{self.canvas_name}_container_id"
        self.views = ViewIds(self)

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

    def tree_id(self, qid: str = "", *, tree: TreeName) -> str:
        return f"{qid}{self.canvas_name}_{tree}"

    def view_id(self, qid: str = "", *, view: ViewName) -> str:
        return f"{qid}{self.canvas_name}_{view}"
