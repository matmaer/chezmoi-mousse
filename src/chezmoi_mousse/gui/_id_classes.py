"""Contains classes to enable setting widget id's without hardcoded strings or
generated the id dynamically when subclassing or to query a widget."""

from dataclasses import dataclass
from enum import Enum

from chezmoi_mousse import (
    Area,
    NavBtn,
    OperateBtn,
    PaneBtn,
    ScreenName,
    TabBtn,
    TreeName,
    ViewName,
)

__all__ = ["Id", "ScreenIds", "Switches", "TabIds"]


class Switches(Enum):
    expand_all = (
        "expand all dirs",
        "Expand all managed directories. Depending on the unchanged switch.",
    )
    unchanged = (
        "show unchanged files",
        "Include files unchanged files which are not found in the 'chezmoi status' output.",
    )
    unmanaged_dirs = (
        "show unmanaged dirs",
        "The default (disabled), only shows directories which already contain managed files. This allows spotting new unmanaged files in already managed directories. Enable to show all directories which contain unmanaged files.",
    )
    unwanted = (
        "show unwanted paths",
        "Include files and directories considered as 'unwanted' for a dotfile manager. These include cache, temporary, trash (recycle bin) and other similar files or directories. For example enable this to add files to your repository which are in a directory named '.cache'.",
    )

    @property
    def switch_name(self) -> str:
        return self.name

    @property
    def label(self) -> str:
        return self.value[0]

    @property
    def tooltip(self) -> str:
        return self.value[1]


class TabIds:
    def __init__(self, tab_name: PaneBtn) -> None:
        self.tab_container_id = f"{tab_name}_container_id"
        self.tab_name: str = tab_name.name

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
        return f"{qid}{self.tab_name}_{switch.switch_name}_switch_horizontal"

    def switch_id(self, qid: str = "", *, switch: Switches) -> str:
        return f"{qid}{self.tab_name}_{switch.switch_name}_switch"

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
    add: TabIds = TabIds(PaneBtn.add_tab)
    apply: TabIds = TabIds(PaneBtn.apply_tab)
    config: TabIds = TabIds(PaneBtn.config_tab)
    help: TabIds = TabIds(PaneBtn.help_tab)
    init: TabIds = TabIds(PaneBtn.init_tab)
    logs: TabIds = TabIds(PaneBtn.logs_tab)
    re_add: TabIds = TabIds(PaneBtn.re_add_tab)
    operate_screen: ScreenIds = ScreenIds(ScreenName.operate)
    maximized_screen: ScreenIds = ScreenIds(ScreenName.maximized)
    install_help_screen: ScreenIds = ScreenIds(ScreenName.install_help)
