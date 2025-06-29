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
    add_directory_btn = "Chezmoi Add Files"
    add_file_btn = "Chezmoi Add File"
    apply_directory_btn = "Chezmoi Apply Files"
    apply_file_btn = "Chezmoi Apply"
    re_add_directory_btn = "Chezmoi Re-Add Files"
    re_add_file_btn = "Chezmoi Re-Add File"
    cancel_apply_btn = "Cancel Apply"
    cancel_re_add_btn = "Cancel Re-Add"
    cancel_add_btn = "Cancel Add"


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
    contents_view = auto()


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
    bullet = "\N{BULLET}"
    burger = "\N{IDENTICAL TO}"
    check_mark = "\N{HEAVY CHECK MARK}"
    gear = "\N{GEAR}"
    apply = f"local \N{LEFTWARDS ARROW}{'\N{EM DASH}' * 3} chezmoi apply"
    re_add = (
        f"chezmoi re-add local {'\N{EM DASH}' * 3}\N{RIGHTWARDS ARROW} chezmoi"
    )
    add = f"chezmoi add local {'\N{EM DASH}' * 3}\N{RIGHTWARDS ARROW} chezmoi"


class TcssStr(StrEnum):
    # Main tabs classes
    collapsible_container = auto()
    dir_tree_widget = auto()
    operate_auto_warning = auto()
    operate_buttons_horizontal = auto()
    operate_collapsible = auto()
    operate_container = auto()
    operate_log = auto()
    operate_screen = auto()
    operate_top_path = auto()
    tab_left_vertical = auto()
    tab_right_vertical = auto()
    top_border_title = auto()

    # Container classes
    content_switcher_left = auto()
    content_switcher_right = auto()
    filter_horizontal = auto()
    filter_label = auto()
    filters_vertical = auto()
    padding_bottom_once = auto()
    single_button_vertical = auto()
    tab_buttons_horizontal = auto()

    # GUI classes
    flow_diagram = auto()

    # Widget classes
    tree_widget = auto()


@dataclass
class LogTabEntry:
    long_command: tuple[str, ...]
    message: str = "no message was provided"


class IdMixin:
    def __init__(self, tab_str: TabStr) -> None:
        self.filter_slider_id = f"{tab_str}_filter_slider"
        self.filter_slider_qid = f"#{self.filter_slider_id}"
        self.tab_main_horizontal_id = f"{tab_str}_main_horizontal"
        self.tab_main_horizontal_qid = f"#{tab_str}_main_horizontal"
        self.tab_name: TabStr = tab_str

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
