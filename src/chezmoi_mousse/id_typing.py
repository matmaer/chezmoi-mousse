from typing import TYPE_CHECKING, Literal, Protocol, TypeVar

# Type aliases not to be imported or used directly
type OperationButtonLabel = Literal[
    "Add Directory",
    "Add File",
    "Apply Directory",
    "Apply File",
    "Re-Add Directory",
    "Re-Add File",
]
type TreeName = Literal["AddTree", "ExpandedTree", "FlatTree", "ManagedTree"]
type TabButtonLabel = Literal["Tree", "List", "Contents", "Diff", "Git-Log"]
type VerticalAreaName = Literal["Left", "Right"]
type SquareAreaName = Literal["TopLeft", "TopRight", "BottomRight"]

# Type aliases to be used instead of the above
type Area = Literal[VerticalAreaName, SquareAreaName]
type ButtonLabel = Literal[TabButtonLabel, OperationButtonLabel]
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
        def button_id(self, some_id: str) -> str: ...
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

    def button_id(self, button_label: ButtonLabel) -> str:
        # replace spaces with underscores to make it a valid id
        button_id = button_label.replace(" ", "_")
        return f"{self.tab_name}_{button_id}_button"

    def buttons_horizontal_id(self, area: Area) -> str:
        return f"{self.tab_name}_{area}_buttons_horizontal"

    def button_vertical_id(self, button_label: ButtonLabel) -> str:
        """Generate an id for each button in a vertical container to center
        them by applying auto width and align on this container."""
        button_id = button_label.replace(" ", "_")
        return f"{self.tab_name}_{button_id}_button_vertical"

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
        """Generate an id for the main left and right vertical containers in a
        tab."""
        return f"{self.tab_name}_{area}_vertical"
