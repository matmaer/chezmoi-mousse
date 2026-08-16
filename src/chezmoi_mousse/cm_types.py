from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from pathlib import Path
    from types import MappingProxyType
    from typing import Any

    from textual.widgets.tree import TreeNode

    from chezmoi_mousse.named_tuples import CommandResult, ScanDirItem
    from chezmoi_mousse.str_enums import PathKind, StatusCode

    type ChangedStatus = dict[Path, tuple[str, str]]  # old, new
    type MinWaitReturn = Callable[..., Awaitable[CommandResult | None]]
    type ParsedJson = dict[str, Any]
    type PathKindMap = MappingProxyType[Path, PathKind]
    type ScanDirResult = list[ScanDirItem] | PathKind
    type StatusMap = MappingProxyType[Path, StatusCode]
    type StatusPairDict = dict[Path, str]  # str containing the status pair
    type StrTuple = tuple[str, ...]
    type TreeNodeDict = dict[Path, TreeNode[Path]]


__all__ = [
    "ChangedStatus",
    "MinWaitReturn",
    "ParsedJson",
    "PathKindMap",
    "ScanDirResult",
    "StatusMap",
    "StatusPairDict",
    "StrTuple",
    "TreeNodeDict",
]
