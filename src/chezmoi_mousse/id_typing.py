from dataclasses import dataclass
from enum import Enum, StrEnum, auto
from pathlib import Path
from typing import Any


# needed by both widgets.py and overrides.py
@dataclass
class NodeData:
    path: Path
    found: bool
    status: str


type CmdWords = tuple[str, ...]
type ParsedJson = dict[str, Any]
type StatusDict = dict[Path, str]


class InputOutputVerbs(StrEnum):
    doctor = auto()
    managed = auto()
    status = auto()


class ReadVerbs(Enum):
    cat = "cat"
    data = "data"
    cat_config = "cat-config"
    diff = "diff"
    git = "git"
    ignored = "ignored"
    source_path = "source-path"


class OperateVerbs(Enum):
    add = "add"
    apply = "apply"
    destroy = "destroy"
    forget = "forget"
    re_add = "re-add"


class CharsEnum(Enum):
    add = f"chezmoi add local {'\N{EM DASH}' * 3}\N{RIGHTWARDS ARROW} chezmoi"
    apply = f"local \N{LEFTWARDS ARROW}{'\N{EM DASH}' * 3} chezmoi apply"
    bullet = "\N{BULLET}"
    burger = "\N{IDENTICAL TO}"
    check_mark = "\N{HEAVY CHECK MARK}"
    x_mark = "\N{HEAVY MULTIPLICATION X}"
    # gear = "\N{GEAR}"
    re_add = (
        f"chezmoi re-add local {'\N{EM DASH}' * 3}\N{RIGHTWARDS ARROW} chezmoi"
    )
    warning_sign = "\N{WARNING SIGN}"


class ButtonEnum(Enum):
    # tab buttons within a tab
    contents_btn = "Contents"
    diff_btn = "Diff"
    git_log_btn = "Git-Log"
    list_btn = "List"
    tree_btn = "Tree"
    # general operational buttons, does not include add as we're immediately
    # rendering add_file_btn or add_dir_btn because forget and destroy
    # operations are not relevant
    # chezmoi_apply_btn = "Chezmoi Apply"
    # chezmoi_destroy_btn = "Chezmoi Destroy"
    # chezmoi_forget_btn = "Chezmoi Forget"
    # chezmoi_re_add_btn = "Chezmoi Re-Add"
    # operational buttons in Operate modal screen
    add_dir_btn = "Add Dir"
    add_file_btn = "Add File"
    # apply_dir_btn = "Apply Dir"
    apply_file_btn = "Apply File"
    # destroy_dir_btn = "Destroy Dir"
    destroy_file_btn = "Destroy File"
    # forget_dir_btn = "Forget Dir"
    forget_file_btn = "Forget File"
    operate_dismiss_btn = "Cancel"
    # re_add_dir_btn = "Re-Add Dir"
    re_add_file_btn = "Re-Add File"


class TabStr(StrEnum):
    apply_tab = auto()
    re_add_tab = auto()
    add_tab = auto()
    init_tab = auto()
    doctor_tab = auto()
    log_tab = auto()


class PaneEnum(Enum):
    add = TabStr.add_tab
    apply = TabStr.apply_tab
    doctor = TabStr.doctor_tab
    init = TabStr.init_tab
    log = TabStr.log_tab
    re_add = TabStr.re_add_tab


class ScreenStr(StrEnum):
    maximized_modal = auto()
    operate_modal = auto()


class ViewStr(StrEnum):
    diff_view = auto()
    git_log_view = auto()
    contents_view = auto()


class Location(StrEnum):
    top = auto()
    right = auto()
    bottom = auto()
    left = auto()


class TreeStr(StrEnum):
    add_tree = auto()
    expanded_tree = auto()
    flat_tree = auto()
    managed_tree = auto()


class FilterEnum(Enum):
    expand_all = "expand all"
    unchanged = "show unchanged"
    unwanted = "show unwanted paths"
    unmanaged_dirs = "show unmanaged dirs"


class TcssStr(StrEnum):
    collapsible_container = auto()
    content_switcher_left = auto()
    content_switcher_right = auto()
    dir_tree_widget = auto()
    doctor_vertical = auto()
    doctor_collapsible = auto()
    doctor_table = auto()
    filter_horizontal = auto()
    filter_label = auto()
    filters_vertical = auto()
    filter_horizontal_pad_bottom = auto()
    flow_diagram = auto()
    last_clicked = auto()
    modal_view = auto()
    operate_auto_warning = auto()
    operate_button = auto()
    operate_collapsible = auto()
    operate_container = auto()
    op_log = auto()
    operate_top_path = auto()
    operate_diff = auto()
    single_button_vertical = auto()
    tab_button = auto()
    tab_buttons_horizontal = auto()
    tab_left_vertical = auto()
    tab_right_vertical = auto()
    top_border_title = auto()
    tree_widget = auto()


class OperateIdStr(StrEnum):
    operate_collapsible_id = auto()
    operate_log_id = auto()
    operate_vertical_id = auto()


class IdMixin:
    def __init__(self, tab_name: TabStr) -> None:
        self.filter_slider_id = f"{tab_name}_filter_slider"
        self.filter_slider_qid = f"#{self.filter_slider_id}"
        self.tab_main_horizontal_id = f"{tab_name}_main_horizontal"
        self.tab_main_horizontal_qid = f"#{self.tab_main_horizontal_id}"
        self.tab_name: TabStr = tab_name

    def button_id(self, button_label: ButtonEnum) -> str:
        return f"{self.tab_name}_{button_label.name}"

    def button_qid(self, button_label: ButtonEnum) -> str:
        return f"#{self.button_id(button_label)}"

    def buttons_horizontal_id(self, location: Location) -> str:
        return f"{self.tab_name}_{location}_horizontal"

    def button_vertical_id(self, button_label: ButtonEnum) -> str:
        return f"{self.tab_name}_{button_label.name}_vertical"

    def content_switcher_id(self, side: Location) -> str:
        return f"{self.tab_name}_{side}_content_switcher"

    def content_switcher_qid(self, side: Location) -> str:
        return f"#{self.content_switcher_id(side)}"

    def filter_horizontal_id(
        self, filter_enum: FilterEnum, location: Location
    ) -> str:
        return (
            f"{self.tab_name}_{filter_enum.name}_filter_horizontal_{location}"
        )

    def filter_horizontal_qid(
        self, filter_enum: FilterEnum, location: Location
    ) -> str:
        return f"#{self.filter_horizontal_id(filter_enum, location)}"

    def switch_id(self, filter_enum: FilterEnum) -> str:
        return f"{self.tab_name}_{filter_enum.name}_switch"

    def switch_qid(self, filter_enum: FilterEnum) -> str:
        return f"#{self.switch_id(filter_enum)}"

    def tab_vertical_id(self, side: Location) -> str:
        return f"{self.tab_name}_{side}_vertical"

    def tab_vertical_qid(self, side: Location) -> str:
        return f"#{self.tab_vertical_id(side)}"

    def tree_id(self, tree: TreeStr) -> str:
        return f"{self.tab_name}_{tree}"

    def tree_qid(self, tree: TreeStr) -> str:
        return f"#{self.tree_id(tree)}"

    def view_id(self, view_enum: ViewStr, operate: bool = False) -> str:
        if operate is True:
            return f"{self.tab_name}_{view_enum}_operate_modal"
        return f"{self.tab_name}_{view_enum}"

    def view_qid(self, view_enum: ViewStr, operate: bool = False) -> str:
        if operate is True:
            return f"#{self.view_id(view_enum)}_operate_modal"
        return f"#{self.view_id(view_enum)}"
