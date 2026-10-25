from __future__ import annotations

import codecs
import re
from itertools import islice
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse import store
from chezmoi_mousse.data_types import DirData, IterDirResult, NodeData
from chezmoi_mousse.str_enums import PathFilters

if TYPE_CHECKING:
    from collections.abc import Iterable


def sort_paths(paths: Iterable[Path]) -> list[Path]:
    path_list = list(paths)
    path_list.sort(key=lambda p: (len(p.parts), str(p).lower()))
    return path_list


def sort_path_dict[V](path_dict: dict[Path, V]) -> dict[Path, V]:
    sorted_keys = sort_paths(path_dict.keys())
    return {path: path_dict[path] for path in sorted_keys}


def parse_paths(path_strings: list[str]) -> list[Path]:
    parsed = [Path(line) for line in path_strings]
    return sort_paths(parsed)


def any_nested_in(*, dir_path: Path, check_paths: Iterable[Path]) -> bool:
    return any(
        path != dir_path and path.is_relative_to(dir_path) for path in check_paths
    )


def get_common_top_level(paths: Iterable[Path]) -> set[Path]:
    """Return the unique top-level parent paths from the provided paths."""
    path_set = paths if isinstance(paths, set) else set(paths)
    return {p for p in path_set if path_set.isdisjoint(p.parents)}


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
    except OSError:
        return False


# Control bytes that never show up in text files. Allowed: bell, backspace, tab, LF,
# VT, FF, CR and ESC (ANSI colors), everything else below 0x20 plus DEL is not text.
_BINARY_BYTES_RE = re.compile(rb"[\x00-\x06\x0e-\x1a\x1c-\x1f\x7f]")
_TEXT_BOMS = (
    codecs.BOM_UTF8,
    codecs.BOM_UTF32_LE,  # before UTF-16 LE, which is its prefix
    codecs.BOM_UTF32_BE,
    codecs.BOM_UTF16_LE,
    codecs.BOM_UTF16_BE,
)


def _file_is_binary(file_path: Path) -> bool:
    try:
        with file_path.open("rb") as f:
            data = f.read(8192)
    except OSError:
        return True  # if we can't read it, return True to treat it as unwanted

    # UTF-16/32 text is full of null bytes, a BOM identifies it as text
    if data.startswith(_TEXT_BOMS):
        return False

    # Working on raw bytes avoids decoding errors on a multi-byte character cut off
    # by the read limit, and on text in legacy encodings. All bytes of a UTF-8
    # multi-byte character are >= 0x80, so they never match.
    return _BINARY_BYTES_RE.search(data) is not None


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


def get_rel_path_str(path: Path) -> str:
    try:
        dest_dir = store.cfg.dest_dir
    except AttributeError:
        dest_dir = None
    if dest_dir is None or path == dest_dir:
        return str(path)
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
    if dir_path == store.cfg.dest_dir:
        return False
    return (
        _path_seems_cache(dir_path)
        or _dir_name_is_unwanted(dir_path)
        or _dir_is_git_objects(dir_path)
        or _dir_has_many_children(dir_path)
    )


def get_un_man_children(dir_path: Path) -> IterDirResult:
    assert dir_path.is_absolute()
    error = ""
    dirs: dict[Path, NodeData] = {}
    files: dict[Path, NodeData] = {}
    for path in dir_path.iterdir():
        if path.is_symlink():
            continue
        try:
            if path.is_dir():
                children = path.iterdir()
                empty_dir = not any(children)
                nested_wanted = False
                if empty_dir:
                    nested_unmanaged = False
                else:
                    nested_unmanaged = True
                    for p in children:
                        if p.is_symlink():
                            continue
                        elif (p.is_dir() and not is_unwanted_dir(p)) or (
                            p.is_file() and not is_unwanted_file(p)
                        ):
                            nested_wanted = True
                            break
                dirs[path] = NodeData(
                    dir_data=DirData(
                        dest_dir=False,
                        empty=empty_dir,
                        nested_managed=False,
                        nested_status=False,
                        nested_un_managed=nested_unmanaged,
                        nested_wanted=nested_wanted,
                    ),
                    dir_path=True,
                    exists=True,
                    managed=False,
                    path=path,
                    source_path=None,
                    status=None,
                    wanted=not is_unwanted_dir(path),
                )
            elif path.is_file():
                files[path] = NodeData(
                    dir_path=False,
                    exists=True,
                    managed=False,
                    path=path,
                    source_path=None,
                    status=None,
                    wanted=not is_unwanted_file(path),
                )
        except OSError as exception:
            error = str(exception)

    return IterDirResult(
        error=error, dirs=sort_path_dict(dirs), files=sort_path_dict(files)
    )
