from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from pathlib import Path

    from textual.widgets.tree import TreeNode

    from chezmoi_mousse.named_tuples import (
        AffectedPaths,
        CommandResult,
        PathStatus,
        ScanDirItem,
    )
    from chezmoi_mousse.str_enums import PathKind

    type MinWaitReturn = Callable[..., Awaitable[AffectedPaths | CommandResult | None]]
    type PathKindMap = dict[Path, PathKind]
    type PathStatusMap = dict[Path, PathStatus]
    type ScanDirResult = list[ScanDirItem] | PathKind
    type StrTuple = tuple[str, ...]
    type TreeNodeDict = dict[Path, TreeNode[Path]]


__all__ = [
    "MinWaitReturn",
    "PathKindMap",
    "PathStatusMap",
    "ScanDirResult",
    "StrTuple",
    "TreeNodeDict",
]
