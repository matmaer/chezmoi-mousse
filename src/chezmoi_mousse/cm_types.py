from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from pathlib import Path
    from types import MappingProxyType
    from typing import Any

    from textual.widgets.tree import TreeNode

    from chezmoi_mousse.named_tuples import CommandResult, ScanDirItem
    from chezmoi_mousse.str_enums import PathKind, StatusCode

    type MinWaitReturn = Callable[..., Awaitable[CommandResult | None]]
    type ScanDirResult = list[ScanDirItem] | PathKind
    type ParsedJson = dict[str, Any]
    type PathKindMap = MappingProxyType[Path, PathKind]
    type StatusMap = MappingProxyType[Path, StatusCode]
    type StrTuple = tuple[str, ...]
    type TreeNodeDict = dict[Path, TreeNode[Path]]


__all__ = [
    "MinWaitReturn",
    "ScanDirResult",
    "ParsedJson",
    "PathKindMap",
    "StatusMap",
    "StrTuple",
    "TreeNodeDict",
]
