from dataclasses import dataclass
from enum import Enum, StrEnum, auto


class ButtonEnum(Enum):
    # tab buttons within a tab
    tree_btn = "Tree"
    list_btn = "List"
    contents_btn = "Contents"
    diff_btn = "Diff"
    git_log_btn = "Git-Log"
    # operational buttons
    add_directory_btn = "Add Directory"
    add_file_btn = "Add File"
    apply_directory_btn = "Apply Directory"
    apply_file_btn = "Apply File"
    re_add_directory_btn = "Re-Add Directory"
    re_add_file_btn = "Re-Add File"


class TabStr(StrEnum):
    apply_tab = auto()
    re_add_tab = auto()
    add_tab = auto()
    doctor_tab = auto()
    diagram_tab = auto()
    log_tab = auto()


class PaneEnum(Enum):
    apply = TabStr.apply_tab
    re_add = TabStr.re_add_tab
    add = TabStr.add_tab
    doctor = TabStr.doctor_tab
    diagram = TabStr.diagram_tab
    log = TabStr.log_tab


class ViewStr(StrEnum):
    diff_view = auto()
    git_log_view = auto()
    path_view = auto()


class SideStr(StrEnum):
    left = auto()
    right = auto()


class CornerStr(StrEnum):
    top_left = auto()
    top_right = auto()
    bottom_right = auto()
    bottom_left = auto()


class TreeStr(StrEnum):
    add_tree = auto()
    expanded_tree = auto()
    flat_tree = auto()
    managed_tree = auto()
    re_add_tree = auto()


class FilterEnum(Enum):
    expand_all = "expand all"
    unchanged = "show unchanged"
    unwanted = "show unwanted paths"
    unmanaged_dirs = "show unmanaged dirs"


class CharsEnum(Enum):
    bullet = "\N{BULLET}"  # code point U+2022
    burger = "\N{IDENTICAL TO}"  # code point U+2261
    check_mark = "\N{HEAVY CHECK MARK}"  # code point U+2714
    gear = "\N{GEAR}"  # code point U+2699


@dataclass
class CommandLogEntry:
    long_command: tuple[str, ...]
    message: str = "no message was provided"


class IdMixin:
    def __init__(self, tab_str: TabStr) -> None:
        self.filter_slider_id = f"{tab_str}_filter_slider"
        self.filter_slider_qid = f"#{self.filter_slider_id}"
        self.tab_main_horizontal_id = f"{tab_str}_main_horizontal"
        self.tab_main_horizontal_qid = f"#{tab_str}_main_horizontal"
        self.tab_name: str = tab_str

    def button_id(self, button_label: ButtonEnum) -> str:
        return f"{self.tab_name}_{button_label.name}"

    def button_qid(self, button_label: ButtonEnum) -> str:
        return f"#{self.button_id(button_label)}"

    def buttons_horizontal_id(self, corner: CornerStr) -> str:
        return f"{self.tab_name}_{corner}_horizontal"

    def button_vertical_id(self, button_label: ButtonEnum) -> str:
        return f"{self.tab_name}_{button_label.name}_vertical"

    def content_switcher_id(self, side: SideStr) -> str:
        return f"{self.tab_name}_{side}_content_switcher"

    def content_switcher_qid(self, side: SideStr) -> str:
        return f"#{self.content_switcher_id(side)}"

    def filter_horizontal_id(self, filter_enum: FilterEnum) -> str:
        return f"{self.tab_name}_{filter_enum.name}_filter_horizontal"

    def switch_id(self, filter_enum: FilterEnum) -> str:
        return f"{self.tab_name}_{filter_enum.name}_switch"

    def switch_qid(self, filter_enum: FilterEnum) -> str:
        return f"#{self.switch_id(filter_enum)}"

    def tab_vertical_id(self, side: SideStr) -> str:
        return f"{self.tab_name}_{side}_vertical"

    def tab_vertical_qid(self, side: SideStr) -> str:
        return f"#{self.tab_vertical_id(side)}"

    def tree_id(self, tree: TreeStr) -> str:
        return f"{self.tab_name}_{tree}_tree"

    def tree_qid(self, tree: TreeStr) -> str:
        return f"#{self.tree_id(tree)}"

    def view_id(self, view_enum: ViewStr) -> str:
        return f"{self.tab_name}_{view_enum}"

    def view_qid(self, view_enum: ViewStr) -> str:
        return f"#{self.view_id(view_enum)}"
