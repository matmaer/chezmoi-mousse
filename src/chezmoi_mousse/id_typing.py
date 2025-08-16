from dataclasses import dataclass
from enum import Enum, StrEnum, auto
from pathlib import Path
from typing import Any

type CmdWords = tuple[str, ...]
type Mro = tuple[type, ...]
type ParsedJson = dict[str, Any]
type StatusDict = dict[Path, str]


# needed by both widgets.py and overrides.py
@dataclass
class NodeData:
    path: Path
    found: bool
    status: str


class IoVerbs(Enum):
    doctor = "doctor"
    managed = "managed"
    status = "status"


class ReadVerbs(Enum):
    cat = "cat"
    cat_config = "cat-config"
    data = "data"
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


class Chars(Enum):
    add = f"local{'\u2014' * 3}\u2192 chezmoi"  # '\N{EM DASH}', '\N{RIGHTWARDS ARROW}'
    apply = f"local \u2190{'\u2014' * 3} chezmoi"  # '\N{LEFTWARDS ARROW}', '\N{EM DASH}'
    bullet = "\u2022"  # '\N{BULLET}'
    burger = "\u2261"  # '\N{IDENTICAL TO}'
    check_mark = "\u2714"  # '\N{HEAVY CHECK MARK}'
    x_mark = "\u2716"  # '\N{HEAVY MULTIPLICATION X}'
    # gear = "\u2699"  # '\N{GEAR}'
    re_add = f"local {'\u2014' * 3}\u2192 chezmoi"  # '\N{EM DASH}', '\N{RIGHTWARDS ARROW}'
    warning_sign = "\u26a0"  # '\N{WARNING SIGN}'
    lower_3_8ths_block = "\u2583"  # "\N{LOWER THREE EIGHTHS BLOCK}"


class Buttons(Enum):
    # tab buttons within a tab
    contents_btn = "Contents"
    diff_btn = "Diff"
    git_log_btn = "Git-Log"
    list_btn = "List"
    tree_btn = "Tree"
    # operational buttons in Operate modal screen
    add_dir_btn = "Add Dir"
    add_file_btn = "Add File"
    apply_file_btn = "Apply File"
    destroy_file_btn = "Destroy File"
    forget_file_btn = "Forget File"
    operate_dismiss_btn = "Cancel"
    re_add_file_btn = "Re-Add File"


class TabStr(StrEnum):
    add_tab = auto()
    apply_tab = auto()
    doctor_tab = auto()
    init_tab = auto()
    log_tab = auto()
    re_add_tab = auto()


class Panes(Enum):
    add = TabStr.add_tab
    apply = TabStr.apply_tab
    doctor = TabStr.doctor_tab
    init = TabStr.init_tab
    log = TabStr.log_tab
    re_add = TabStr.re_add_tab


class ViewStr(StrEnum):
    contents_view = auto()
    diff_view = auto()
    doctor_table = auto()
    git_log_view = auto()


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


@dataclass(frozen=True)
class FilterData:
    label: str
    tooltip: str


class Filters(Enum):
    unmanaged_dirs = FilterData(
        "show unmanaged dirs",
        (
            "The default (disabled), only shows directories which already "
            "contain managed files. This allows spotting new unmanaged files "
            "in already managed directories. Enable to show all directories "
            "which contain unmanaged files."
        ),
    )
    unwanted = FilterData(
        "show unwanted paths",
        (
            "Include files and directories considered as 'unwanted' for a "
            "dotfile manager. These include cache, temporary, trash (recycle "
            "bin) and other similar files or directories. For example enable "
            "this to add files to your chezmoi repository which are in a "
            "directory named '.cache'."
        ),
    )
    unchanged = FilterData(
        "show unchanged files",
        (
            "Include files unchanged files which are not found in the "
            "'chezmoi status' output."
        ),
    )
    expand_all = FilterData(
        "expand all dirs",
        (
            "Expand all managed directories. Depending on the unchanged "
            "switch."
        ),
    )


class TcssStr(StrEnum):
    content_switcher_left = auto()
    content_switcher_right = auto()
    dir_tree_widget = auto()
    doctor_collapsible = auto()
    doctor_table = auto()
    doctor_vertical = auto()
    filter_horizontal = auto()
    filter_label = auto()
    filters_vertical = auto()
    flow_diagram = auto()
    last_clicked = auto()
    modal_base = auto()
    modal_container = auto()
    op_log = auto()
    operate_auto_warning = auto()
    operate_button = auto()
    operate_top_path = auto()
    pad_bottom = auto()
    single_button_vertical = auto()
    tab_button = auto()
    tab_buttons_horizontal = auto()
    tab_left_vertical = auto()
    tab_right_vertical = auto()
    top_border_title = auto()
    tree_widget = auto()


class ModalIdStr(StrEnum):
    maximized_modal = auto()
    maximized_vertical = auto()
    modal_contents_view = auto()
    modal_diff_view = auto()
    modal_git_log_view = auto()
    operate_auto_warning = auto()
    operate_collapsible = auto()
    operate_info = auto()
    operate_log = auto()
    operate_modal = auto()
    operate_vertical = auto()

    @property
    def qid(self) -> str:
        return f"#{self.name}"


class DoctorEnum(Enum):
    doctor = "chezmoi doctor output (diagnostic information)"
    diagram = "chezmoi diagram (how operations are applied)"
    cat_config = "chezmoi cat-config (contents of config-file)"
    doctor_ignored = "chezmoi ignored (git ignore in source-dir)"
    doctor_template_data = "chezmoi template-data (contents of template-file)"

    @property
    def qid(self) -> str:
        return f"#{self.name}"


class IdMixin:
    def __init__(self, tab_name: TabStr) -> None:
        self.filter_slider_id = f"{tab_name}_filter_slider"
        self.filter_slider_qid = f"#{self.filter_slider_id}"
        self.tab_main_horizontal_id = f"{tab_name}_main_horizontal"
        self.tab_name: TabStr = tab_name

    def button_id(self, button_label: Buttons) -> str:
        return f"{self.tab_name}_{button_label.name}"

    def button_qid(self, button_label: Buttons) -> str:
        return f"#{self.button_id(button_label)}"

    def buttons_horizontal_id(self, location: Location) -> str:
        return f"{self.tab_name}_{location}_horizontal"

    def button_vertical_id(self, button_label: Buttons) -> str:
        return f"{self.tab_name}_{button_label.name}_vertical"

    def content_switcher_id(self, side: Location) -> str:
        return f"{self.tab_name}_{side}_content_switcher"

    def content_switcher_qid(self, side: Location) -> str:
        return f"#{self.content_switcher_id(side)}"

    def filter_horizontal_id(
        self, filter_enum: Filters, location: Location
    ) -> str:
        return (
            f"{self.tab_name}_{filter_enum.name}_filter_horizontal_{location}"
        )

    def filter_horizontal_qid(
        self, filter_enum: Filters, location: Location
    ) -> str:
        return f"#{self.filter_horizontal_id(filter_enum, location)}"

    def switch_id(self, filter_enum: Filters) -> str:
        return f"{self.tab_name}_{filter_enum.name}_switch"

    def switch_qid(self, filter_enum: Filters) -> str:
        return f"#{self.switch_id(filter_enum)}"

    def tab_vertical_id(self, side: Location) -> str:
        return f"{self.tab_name}_{side}_vertical"

    def tab_vertical_qid(self, side: Location) -> str:
        return f"#{self.tab_vertical_id(side)}"

    def tree_id(self, tree: TreeStr) -> str:
        return f"{self.tab_name}_{tree}"

    def tree_qid(self, tree: TreeStr) -> str:
        return f"#{self.tree_id(tree)}"

    def view_id(self, view: ViewStr) -> str:
        return f"{self.tab_name}_{view}"

    def view_qid(self, view: ViewStr) -> str:
        return f"#{self.view_id(view)}"
