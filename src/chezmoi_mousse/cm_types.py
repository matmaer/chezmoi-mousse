from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from pathlib import Path
    from types import MappingProxyType
    from typing import Any

    from textual.widgets.tree import TreeNode

    from chezmoi_mousse.named_tuples import AffectedPaths, CommandResult, ScanDirItem
    from chezmoi_mousse.str_enums import PathKind, StatusCode

    type MinWaitReturn = Callable[..., Awaitable[AffectedPaths | CommandResult | None]]
    type ParsedJson = dict[str, Any]
    type PathKindMap = MappingProxyType[Path, PathKind]
    type ScanDirResult = list[ScanDirItem] | PathKind
    type StatusMap = MappingProxyType[Path, StatusCode]
    type StrTuple = tuple[str, ...]
    type TreeNodeDict = dict[Path, TreeNode[Path]]


__all__ = [
    "MinWaitReturn",
    "ParsedJson",
    "PathKindMap",
    "ScanDirResult",
    "StatusMap",
    "StrTuple",
    "TreeNodeDict",
]
