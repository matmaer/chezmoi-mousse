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
    add_file_btn = "Chezmoi Add File"
    apply_file_btn = "Chezmoi Apply"
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

    def operate_info(self) -> str:
        # info text currently used for info above the diff or contents in the Operate modal screen.
        info_map = {
            TabStr.apply_tab: "The file will be modified! Red lines will be removed, green lines will be added.",
            TabStr.re_add_tab: "Chezmoi state will be updated! Red lines will be removed, green lines will be added.",
            TabStr.add_tab: "This path will be added to your chezmoi dotfile manager.",
        }
        return info_map.get(self, "")


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


class CharsEnum(Enum):
    bullet = "\N{BULLET}"
    burger = "\N{IDENTICAL TO}"
    # check_mark = "\N{HEAVY CHECK MARK}"
    # gear = "\N{GEAR}"
    apply = f"local \N{LEFTWARDS ARROW}{'\N{EM DASH}' * 3} chezmoi apply"
    re_add = (
        f"chezmoi re-add local {'\N{EM DASH}' * 3}\N{RIGHTWARDS ARROW} chezmoi"
    )
    add = f"chezmoi add local {'\N{EM DASH}' * 3}\N{RIGHTWARDS ARROW} chezmoi"


class TcssStr(StrEnum):
    collapsible_container = auto()
    content_switcher_left = auto()
    content_switcher_right = auto()
    dir_tree_widget = auto()
    filter_horizontal = auto()
    filter_label = auto()
    filters_vertical = auto()
    filter_horizontal_pad_bottom = auto()
    flow_diagram = auto()
    last_clicked = auto()
    modal_view = auto()
    operate_auto_warning = auto()
    operate_button = auto()
    operate_buttons_horizontal = auto()
    operate_collapsible = auto()
    operate_container = auto()
    operate_log = auto()
    operate_screen = auto()
    operate_top_path = auto()
    operate_diff = auto()
    single_button_vertical = auto()
    tab_button = auto()
    tab_buttons_horizontal = auto()
    tab_left_vertical = auto()
    tab_right_vertical = auto()
    top_border_title = auto()
    tree_widget = auto()


# added here to make the logic in test_no_hardcoded_ids work for all modules
class SplashIdStr(StrEnum):
    animated_fade_id = auto()
    loading_screen_id = auto()
    splash_rich_log_id = auto()


class OperateIdStr(StrEnum):
    operate_collapsible_id = auto()
    operate_info_id = auto()
    operate_log_id = auto()
    operate_screen_id = auto()
    operate_top_path_id = auto()
    operate_vertical_id = auto()


@dataclass
class LogTabEntry:
    long_command: tuple[str, ...]
    message: str = "no message was provided"


class IdMixin:
    def __init__(self, tab_str: TabStr) -> None:
        self.filter_slider_id = f"{tab_str}_filter_slider"
        self.filter_slider_qid = f"#{self.filter_slider_id}"
        self.tab_main_horizontal_id = f"{tab_str}_main_horizontal"
        self.tab_main_horizontal_qid = f"#{self.tab_main_horizontal_id}"
        self.tab_name: TabStr = tab_str

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
