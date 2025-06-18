from enum import Enum
from typing import TYPE_CHECKING, Literal, Protocol, TypeVar


class TabButton(Enum):
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


type TreeName = Literal["AddTree", "ExpandedTree", "FlatTree", "ManagedTree"]
type VerticalAreaName = Literal["Left", "Right"]
type SquareAreaName = Literal["TopLeft", "TopRight", "BottomRight"]


type Area = Literal[VerticalAreaName, SquareAreaName]
type ComponentName = Literal[TreeName, "PathView", "DiffView", "GitLog"]
type FilterName = Literal[
    "expand_all", "unchanged", "unwanted", "unmanaged_dirs"
]
type TabName = Literal["Apply", "ReAdd", "Add", "Doctor", "Diagram", "Log"]

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
        def button_id(self, some_id: TabButton) -> str: ...
        def content_switcher_id(self, some_id: str) -> str: ...
        def component_id(self, some_id: str) -> str: ...
        def filter_switch_id(self, some_id: str) -> str: ...

else:
    # Runtime-compatible empty Protocol
    class CommonTabEvents(Protocol): ...


class IdMixin:
    def __init__(self, tab: TabName) -> None:
        self.tab_name: TabName = tab
        self.tab_main_horizontal_id = f"{self.tab_name}_main_horizontal"
        self.filter_slider_id = f"{self.tab_name}_filter_slider"

    def button_id(self, button_label: TabButton) -> str:
        return f"{self.tab_name}_{button_label.name}"

    def buttons_horizontal_id(self, area: Area) -> str:
        return f"{self.tab_name}_{area}_horizontal"

    def button_vertical_id(self, button_label: TabButton) -> str:
        return f"{self.tab_name}_{button_label.name}_vertical"

    def component_id(self, component_name: ComponentName) -> str:
        """Generate an id for items imported from components.py."""
        return f"{self.tab_name}_{component_name}_component"

    def content_switcher_id(self, area: Area) -> str:
        return f"{self.tab_name}_{area}_content_switcher"

    def filter_horizontal_id(self, filter_name: FilterName) -> str:
        return f"{self.tab_name}_{filter_name}_filter_horizontal"

    def filter_label_id(self, filter_name: FilterName) -> str:
        return f"{self.tab_name}_{filter_name}_filter_label"

    def filter_switch_id(self, filter_name: FilterName) -> str:
        return f"{self.tab_name}_{filter_name}_filter_switch"

    def tab_vertical_id(self, area: Area) -> str:
        return f"{self.tab_name}_{area}_vertical"
