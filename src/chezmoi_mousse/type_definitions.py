from typing import Literal, Protocol, TypeVar, overload, Any

T = TypeVar("T")

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
type TabLabel = Literal["Apply", "Re-Add", "Add", "Doctor", "Diagram", "Log"]


class SharedTabEvents(Protocol):
    @overload
    def query_one(self, some_widget_id: str) -> Any: ...
    @overload
    def query_one(
        self, some_widget_id: str, some_textual_type: type[T]
    ) -> T: ...
    def query_one(
        self, some_widget_id: str, some_textual_type: type[T] = ...
    ) -> T: ...
    def button_id(self, label: str) -> str: ...
    def content_switcher_id(self, side: str) -> str: ...
    def component_id(self, label: str) -> str: ...
    def filter_switch_id(self, label: str) -> str: ...
