from enum import Enum, StrEnum, auto
from typing import TYPE_CHECKING, Protocol, TypeVar


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


class MainTab(Enum):
    add_tab = "Add"
    re_add_tab = "Re-Add"
    apply_tab = "Apply"
    doctor_tab = "Doctor"
    diagram_tab = "Diagram"
    log_tab = "Log"


class TabSide(StrEnum):
    left = auto()
    right = auto()


class Corner(StrEnum):
    top_left = auto()
    top_right = auto()
    bottom_right = auto()
    bottom_left = auto()


class Component(StrEnum):
    add_tree = auto()
    re_add_tree = auto()
    expanded_tree = auto()
    flat_tree = auto()
    managed_tree = auto()
    path_view = auto()
    diff_view = auto()
    git_log = auto()


class Filter(Enum):
    expand_all = "expand all"
    unchanged = "show unchanged"
    unwanted = "show unwanted paths"
    unmanaged_dirs = "show unmanaged dirs"


class Chars(Enum):
    burger = "\N{IDENTICAL TO}"  # code point U+2261
    gear = "\N{GEAR}"  # code point U+2699
    bullet = "\N{BULLET}"  # code point U+2022
    check_mark = "\N{HEAVY CHECK MARK}"  # code point U+2714


if TYPE_CHECKING:
    from textual.containers import Container
    from textual.widgets import ContentSwitcher, Switch

    from chezmoi_mousse.widgets import (
        DiffView,
        ExpandedTree,
        FlatTree,
        GitLog,
        ManagedTree,
        PathView,
        TreeBase,
    )

    type TreeTabWidget = (
        Container
        | ContentSwitcher
        | DiffView
        | ExpandedTree
        | FlatTree
        | GitLog
        | ManagedTree
        | PathView
        | Switch
        | TreeBase
    )

    T = TypeVar("T", bound="TreeTabWidget")

    class CommonTabEvents(Protocol):

        def query_one(self, some_id: str, this_type: type[T]) -> T: ...
        def button_id(self, some_id: ButtonEnum) -> str: ...
        def content_switcher_id(self, some_id: str) -> str: ...
        def component_id(self, some_id: str) -> str: ...
        def filter_switch_id(self, some_id: str) -> str: ...

else:
    # Runtime-compatible empty Protocol
    class CommonTabEvents(Protocol): ...


class IdMixin:
    def __init__(self, tab_key: MainTab) -> None:
        self.tab_main_horizontal_id = f"{tab_key.name}_main_horizontal"
        self.filter_slider_id = f"{tab_key.name}_filter_slider"
        self.tab_name: str = tab_key.name

    def button_id(self, button_label: ButtonEnum) -> str:
        return f"{self.tab_name}_{button_label.name}"

    def buttons_horizontal_id(self, corner: Corner) -> str:
        return f"{self.tab_name}_{corner}_horizontal"

    def button_vertical_id(self, button_label: ButtonEnum) -> str:
        return f"{self.tab_name}_{button_label.name}_vertical"

    def component_id(self, component: str) -> str:
        """Generate an id for items imported from components.py."""
        return f"{self.tab_name}_{component}_component"

    def content_switcher_id(self, side: TabSide) -> str:
        return f"{self.tab_name}_{side}_content_switcher"

    def filter_horizontal_id(self, filter_name: str) -> str:
        return f"{self.tab_name}_{filter_name}_filter_horizontal"

    def filter_switch_id(self, filter_name: str) -> str:
        return f"{self.tab_name}_{filter_name}_filter_switch"

    def tab_vertical_id(self, side: TabSide) -> str:
        return f"{self.tab_name}_{side}_vertical"
