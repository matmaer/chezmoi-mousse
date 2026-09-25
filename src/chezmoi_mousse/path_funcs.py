from __future__ import annotations

import os
from itertools import islice
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse import store
from chezmoi_mousse.named_tuples import ScanDirResult
from chezmoi_mousse.str_enums import PathFilters, StatusCode

if TYPE_CHECKING:
    from collections.abc import Iterable


def sort_paths(paths: Iterable[Path]) -> list[Path]:
    path_list = list(paths)
    path_list.sort(key=lambda p: (len(p.parts), p))
    return path_list


def sort_path_dict[V](path_dict: dict[Path, V]) -> dict[Path, V]:
    sorted_keys = sort_paths(path_dict.keys())
    return {path: path_dict[path] for path in sorted_keys}


def get_nested_in(
    *, dir_path: Path, check_paths: set[Path] | frozenset[Path]
) -> list[Path]:
    nested_in = [
        path
        for path in check_paths
        if path != dir_path and dir_path.is_relative_to(dir_path)
    ]
    return sort_paths(nested_in)


def any_nested_in(*, dir_path: Path, check_paths: set[Path] | frozenset[Path]) -> bool:
    return any(
        path != dir_path and path.is_relative_to(dir_path) for path in check_paths
    )


def get_sorted_top_parents(
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


def _dir_name_is_unwanted(dir_path: Path) -> bool:
    return dir_path.parts[-1] in PathFilters.UNWANTED_DIRS.value


def _dir_is_git_objects(dir_path: Path) -> bool:
    return dir_path.parts[-1] == "objects" and dir_path.parts[-2] == ".git"


def _dir_has_many_children(dir_path: Path, max_entries: int = 200) -> bool:
    # TODO: make this configurable but 200 entries seems like a reasonable limit
    # for a directory to consider interesting in the context of dotfiles.
    max_entries = max_entries - 1
    try:
        return (
            next(islice(dir_path.iterdir(), max_entries, max_entries + 1), None)
            is not None
        )
    except (PermissionError, FileNotFoundError, OSError):
        return False


def _file_is_binary(file_path: Path) -> bool:
    try:
        with file_path.open("rb") as f:
            data = f.read(1024)
    except OSError:
        return True  # if we can't read it, return True to treat it as unwanted

    if not data:
        return False  # empty files are not considered binary

    if b"\x00" in data:
        return True  # null byte found, likely binary

    try:
        text = data.decode("utf-8-sig")  # decode with BOM handling
    except UnicodeDecodeError:
        return True  # likely binary

    for char in text:
        if char in "\t\n\r":
            continue  # allow common whitespace characters

        code = ord(char)
        if 32 <= code <= 126 or code >= 127:
            continue  # allow printable ASCII and extended characters

        return True  # non-printable character found, likely binary

    return False  # no non-printable characters found, likely text


def _file_is_large(file_path: Path) -> bool:
    try:
        return file_path.stat().st_size > 512 * 1024  # half a megabyte
    except OSError:
        return True  # if we can't stat it, return True to treat it as unwanted


def _file_is_sensitive(file_path: Path) -> bool:
    return (
        file_path.suffix in PathFilters.KEY_FILE_EXTENSIONS.value
        or file_path.parts[-1] in PathFilters.KEY_FILE_NAMES.value
    )


def _file_unwanted_suffix(file_path: Path) -> bool:
    return file_path.suffix in PathFilters.UNWANTED_FILE_SUFFIXES.value


def get_rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    return str(path.relative_to(store.cfg.dest_dir))


def _path_seems_cache(path: Path) -> bool:
    path_parts_lower = [p.lower() for p in path.parts]
    return any(p.startswith("cache") or p.endswith("cache") for p in path_parts_lower)


def is_unwanted_file(file_path: Path) -> bool:
    return (
        _path_seems_cache(file_path)
        or _file_is_sensitive(file_path)
        or _file_unwanted_suffix(file_path)
        or _file_is_large(file_path)
        or _file_is_binary(file_path)
    )


def is_unwanted_dir(dir_path: Path) -> bool:
    return (
        _path_seems_cache(dir_path)
        or _dir_name_is_unwanted(dir_path)
        or _dir_is_git_objects(dir_path)
        or _dir_has_many_children(dir_path)
    )


def os_scan_dir(dir_path: Path) -> ScanDirResult:

    errors: list[str] = []

    try:
        if str(dir_path) == "None":
            errors.append("Received a path named 'None'")
        if not dir_path.is_absolute():
            errors.append("Error, did not receive an absolute path")
        if store.cfg.dest_dir not in dir_path.parents:
            errors.append(
                f"Error, got a directory which is not a child of the destDir "
                f"{store.cfg.dest_dir}"
            )
        if dir_path.is_symlink():
            errors.append(f"Error, the provided path is a symlink: {dir_path}")
        # str(dir_path) to reduce possible exceptions which would be raised by pathlib
        with os.scandir(str(dir_path)) as entry_generator:
            dir_entries: list[os.DirEntry[str]] = list(entry_generator)
        entry_count = len(dir_entries)
        if entry_count > 500:
            errors.append(f"The directory has too many children: {entry_count}")
            return ScanDirResult(
                errors=errors,
                exceptions={},
                symlinks=[],
                dirs={},
                files={},
            )
    except (FileNotFoundError, PermissionError, OSError) as error:
        errors.append(str(error))
        return ScanDirResult(
            errors=errors,
            exceptions={},
            symlinks=[],
            dirs={},
            files={},
        )

    exceptions: dict[Path, str] = {}
    symlinks: list[Path] = []
    dirs: dict[Path, StatusCode] = {}
    files: dict[Path, StatusCode] = {}

    for entry in dir_entries:
        try:
            path = Path(entry.path)
            if path.is_symlink():
                symlinks.append(path)
            if entry.is_dir(follow_symlinks=False):
                if is_unwanted_dir(path):
                    dirs[path] = StatusCode.XX
                else:
                    dirs[path] = StatusCode.UU
            elif entry.is_file(follow_symlinks=False):
                if is_unwanted_file(path):
                    files[path] = StatusCode.XX
                else:
                    files[path] = StatusCode.UU
        except (FileNotFoundError, PermissionError, OSError) as exception:
            exceptions[Path(entry)] = str(exception)

    return ScanDirResult(
        errors=errors,
        exceptions=sort_path_dict(exceptions),
        symlinks=sort_paths(symlinks),
        dirs=sort_path_dict(dirs),
        files=sort_path_dict(files),
    )
