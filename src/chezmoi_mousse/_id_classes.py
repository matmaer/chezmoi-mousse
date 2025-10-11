"""Contains classes to enable setting widget id's without hardcoded strings or
generated the id dynamically when subclassing or to query a widget."""

from dataclasses import dataclass

from chezmoi_mousse._labels import NavBtn, OperateBtn, PaneBtn, TabBtn
from chezmoi_mousse._names import AreaName, TreeName, ViewName
from chezmoi_mousse._switch_data import SwitchData

__all__ = ["TabIds", "Id"]


class TabIds:
    def __init__(self, tab_name: PaneBtn) -> None:
        self.tab_name: str = tab_name.name
        self.tab_container_id = f"{tab_name}_container_id"
        self.operate_container_id = f"{tab_name}_operate_container_id"

        # id's for which there's only one widget for each self.tab_name
        self.datatable_id = f"{tab_name}_datatable"
        self.datatable_qid = f"#{self.datatable_id}"
        self.listview_id = f"{tab_name}_listview"
        self.listview_qid = f"#{self.listview_id}"
        self.switches_slider_id = f"{tab_name}_switches_slider"
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
        return f"{qid}{self.tab_name}_{btn.name}{suffix}"

    def buttons_horizontal_id(self, area: AreaName) -> str:
        return f"{self.tab_name}_{area}_horizontal"

    def content_switcher_id(self, qid: str = "", *, area: AreaName) -> str:
        return f"{qid}{self.tab_name}_{area}_content_switcher"

    def switch_horizontal_id(
        self, qid: str = "", *, switch: SwitchData
    ) -> str:
        return f"{qid}{self.tab_name}_{switch.switch_name}_switch_horizontal"

    def switch_id(self, qid: str = "", *, switch: SwitchData) -> str:
        return f"{qid}{self.tab_name}_{switch.switch_name}_switch"

    def tab_vertical_id(self, qid: str = "", *, area: AreaName) -> str:
        return f"{qid}{self.tab_name}_{area}_vertical"

    def tree_id(self, qid: str = "", *, tree: TreeName) -> str:
        return f"{qid}{self.tab_name}_{tree}"

    def view_id(self, qid: str = "", *, view: ViewName) -> str:
        return f"{qid}{self.tab_name}_{view}"


@dataclass(frozen=True)
class Id:
    add: TabIds = TabIds(PaneBtn.add_tab)
    apply: TabIds = TabIds(PaneBtn.apply_tab)
    config: TabIds = TabIds(PaneBtn.config_tab)
    help: TabIds = TabIds(PaneBtn.help_tab)
    init: TabIds = TabIds(PaneBtn.init_tab)
    logs: TabIds = TabIds(PaneBtn.logs_tab)
    re_add: TabIds = TabIds(PaneBtn.re_add_tab)
