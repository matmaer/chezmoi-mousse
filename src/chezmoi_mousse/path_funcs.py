from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import chezmoi_mousse._func as _func
from chezmoi_mousse.named_tuples import ScanDirItem

if TYPE_CHECKING:
    from collections.abc import Iterable

type ScanDirResult = list[ScanDirItem]

__all__ = [
    "get_top_parents",
    "is_unwanted_dir",
    "is_unwanted_file",
    "os_scan_dir",
    "sort_path_dict",
    "sort_paths",
]


def sort_paths(paths: Iterable[Path]) -> list[Path]:
    path_list = list(paths)
    path_list.sort(key=lambda p: (len(p.parts), p))
    return path_list


def sort_path_dict[V](path_dict: dict[Path, V]) -> dict[Path, V]:
    sorted_keys = sort_paths(path_dict.keys())
    return {path: path_dict[path] for path in sorted_keys}


def get_top_parents(
    paths: Iterable[Path] | dict[Path, bool],
) -> list[Path]:
    """
    Return the unique top-level parent paths from the proveded collection of paths.
    """
    top_parents: list[Path] = []
    for p in paths:
        if not any(parent in paths for parent in p.parents):
            top_parents.append(p)

    top_parents.sort(key=lambda p: len(p.parts))
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
        return []

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
