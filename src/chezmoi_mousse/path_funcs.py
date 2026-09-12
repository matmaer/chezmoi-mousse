from __future__ import annotations

import os
from pathlib import Path

from chezmoi_mousse import _func
from chezmoi_mousse.named_tuples import (
    ScanDirItem,
)
from chezmoi_mousse.str_enums import (
    PathKind,
)

type ScanDirResult = list[ScanDirItem] | PathKind

__all__ = ["get_top_parents", "is_unwanted_dir", "is_unwanted_file", "os_scan_dir"]


def get_top_parents(paths: list[Path] | set[Path] | frozenset[Path]) -> list[Path]:

    if not paths:
        return []

    sorted_paths = sorted(paths)
    top_parents = [sorted_paths[0]]

    for path in sorted_paths[1:]:
        # Compare current path only to the last confirmed top parent
        if not path.is_relative_to(top_parents[-1]):
            top_parents.append(path)

    return top_parents


def is_unwanted_file(file_path: Path) -> bool:
    return (
        _func.path_seems_cache(file_path)
        or _func.file_is_sensitive(file_path)
        or _func.file_unwanted_suffix(file_path)
        or _func.file_is_large(file_path)
        or _func.file_is_binary(file_path)
    )


def is_unwanted_dir(dir_path: Path) -> bool:
    return (
        _func.path_seems_cache(dir_path)
        or _func.dir_name_is_unwanted(dir_path)
        or _func.dir_is_git_objects(dir_path)
        or _func.dir_has_many_children(dir_path)
    )


def os_scan_dir(dir_path: Path) -> ScanDirResult:

    if not dir_path.is_absolute():
        raise ValueError(
            (
                "This function should only be called with absolute paths as we ",
                "are caching the results.",
            )
        )

    scan_dir_items: list[ScanDirItem] = []
    # str(dir_path) to reduce possible exceptions which would be raised by pathlib
    try:
        with os.scandir(str(dir_path)) as entry_generator:
            dir_entries: list[os.DirEntry[str]] = list(entry_generator)
    except (FileNotFoundError, PermissionError, OSError):
        return PathKind.ERROR

    sibling_count = len(dir_entries)

    for de in dir_entries:
        de_path = Path(de.path)
        is_dir = de.is_dir()
        is_file = de.is_file()
        is_symlink = de.is_symlink()
        file_size = None
        if is_symlink:
            matches_unwanted = True
        elif is_dir:
            matches_unwanted = is_unwanted_dir(de_path)
        elif is_file:
            try:
                file_size = de.stat().st_size
            except OSError:
                file_size = None
                matches_unwanted = True
            else:
                matches_unwanted = is_unwanted_file(de_path)
        else:
            matches_unwanted = True

        if matches_unwanted:
            continue

        scan_dir_items.append(
            ScanDirItem(
                scanned_dir=dir_path,
                path=de_path,
                is_dir=is_dir,
                is_file=is_file,
                is_symlink=is_symlink,
                name=de.name,
                file_size=file_size,
                sibling_count=sibling_count,
                matches_unwanted=matches_unwanted,
            )
        )
    return scan_dir_items
