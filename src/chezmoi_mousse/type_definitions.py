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
    from textual.widgets import Checkbox, ContentSwitcher, Switch

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
        Checkbox
        | Container
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
        def filter_item_id(self, some_id: str) -> str: ...

else:
    # Runtime-compatible empty Protocol
    class CommonTabEvents(Protocol): ...
