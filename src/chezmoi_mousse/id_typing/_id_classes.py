"""Contains classes to enable setting widget id's without hardcoded strings or
generated the id dynamically when subclassing or to query a widget."""

from dataclasses import dataclass, fields
from pathlib import Path

from chezmoi_mousse.id_typing._enums import Switches
from chezmoi_mousse.id_typing._str_enums import (
    Area,
    NavBtn,
    OperateBtn,
    ScreenName,
    TabBtn,
    TabName,
    TreeName,
    ViewName,
)

__all__ = [
    "DirNodeData",
    "FileNodeData",
    "Id",
    "NodeData",
    "ScreenIds",
    "SplashReturnData",
    "TabIds",
]


#############
# dataclasses


@dataclass
class NodeData:
    found: bool
    path: Path
    status: str


@dataclass
class DirNodeData(NodeData):
    pass


@dataclass
class FileNodeData(NodeData):
    pass


@dataclass
class SplashReturnData:
    doctor: str
    dir_status_lines: str
    file_status_lines: str
    managed_dirs: str
    managed_files: str


class TabIds:
    def __init__(self, tab_name: TabName) -> None:
        self.tab_container_id = f"{tab_name}_container_id"
        self.tab_name: TabName = tab_name
        self.tab_pane_id = f"{tab_name}_pane"

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

    def buttons_horizontal_id(self, area: Area) -> str:
        return f"{self.tab_name}_{area}_horizontal"

    def button_vertical_id(self, btn_enum: OperateBtn | TabBtn) -> str:
        return f"{self.tab_name}_{btn_enum.name}_vertical"

    def buttons_vertical_group_id(self, area: Area) -> str:
        return f"{self.tab_name}_{area}_vertical"

    def content_switcher_id(self, qid: str = "", *, area: Area) -> str:
        return f"{qid}{self.tab_name}_{area}_content_switcher"

    def switch_horizontal_id(self, qid: str = "", *, switch: Switches) -> str:
        return f"{qid}{self.tab_name}_{switch.name}_switch_horizontal"

    def switch_id(self, qid: str = "", *, switch: Switches) -> str:
        return f"{qid}{self.tab_name}_{switch.name}_switch"

    def tab_vertical_id(self, qid: str = "", *, area: Area) -> str:
        return f"{qid}{self.tab_name}_{area}_vertical"

    def tree_id(self, qid: str = "", *, tree: TreeName) -> str:
        return f"{qid}{self.tab_name}_{tree}"

    def view_id(self, qid: str = "", *, view: ViewName) -> str:
        return f"{qid}{self.tab_name}_{view}"


class ScreenIds:
    def __init__(self, screen_name: ScreenName) -> None:
        self.screen_name = screen_name
        self.screen_id = f"{screen_name}_id"
        self.border_subtitle_dict = {
            ScreenName.maximized: " double click or escape key to close ",
            ScreenName.operate: " escape key to close ",
            ScreenName.install_help: " escape key to exit app ",
        }

    def border_subtitle(self):
        return self.border_subtitle_dict[self.screen_name]

    def view_id(self, qid: str = "", *, view: ViewName) -> str:
        return f"{qid}{self.screen_name}_{view}"


@dataclass(frozen=True)
class Id:
    add: TabIds = TabIds(TabName.add_tab)
    apply: TabIds = TabIds(TabName.apply_tab)
    config: TabIds = TabIds(TabName.config_tab)
    help: TabIds = TabIds(TabName.help_tab)
    init: TabIds = TabIds(TabName.init_tab)
    logs: TabIds = TabIds(TabName.log_tab)
    re_add: TabIds = TabIds(TabName.re_add_tab)
    operate_screen: ScreenIds = ScreenIds(ScreenName.operate)
    maximized_screen: ScreenIds = ScreenIds(ScreenName.maximized)
    install_help_screen: ScreenIds = ScreenIds(ScreenName.install_help)

    _pane_id_map: dict[str, TabIds] | None = None

    @classmethod
    def get_tab_ids_from_pane_id(cls, pane_id: str) -> TabIds:

        if cls._pane_id_map is None:
            cls._pane_id_map = {}
            for field in fields(cls):
                field_value = getattr(cls, field.name)
                if isinstance(field_value, TabIds):
                    cls._pane_id_map[field_value.tab_pane_id] = field_value

        if pane_id in cls._pane_id_map:
            return cls._pane_id_map[pane_id]
        raise ValueError(f"No TabIds found for pane_id: {pane_id}")
