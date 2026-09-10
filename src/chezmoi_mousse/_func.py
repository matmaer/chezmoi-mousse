from __future__ import annotations

from itertools import islice
from typing import TYPE_CHECKING

from chezmoi_mousse import store
from chezmoi_mousse.str_enums import PathFilters, ReadCmd

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.str_enums import WriteCmd


__all__ = [
    "file_is_binary",
    "file_is_large",
    "file_is_sensitive",
    "file_unwanted_suffix",
    "get_base_cmd",
    "get_full_cmd",
    "get_rel_path",
    "path_seems_cache",
]


def dir_name_is_unwanted(dir_path: Path) -> bool:
    return dir_path.parts[-1] in PathFilters.UNWANTED_DIRS.value


def dir_is_git_objects(dir_path: Path) -> bool:
    return dir_path.parts[-1] == "objects" and dir_path.parts[-2] == ".git"


def dir_has_many_children(dir_path: Path, max_entries: int = 200) -> bool:
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


def file_is_binary(file_path: Path) -> bool:
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


def file_is_large(file_path: Path) -> bool:
    try:
        return file_path.stat().st_size > 512 * 1024  # half a megabyte
    except OSError:
        return True  # if we can't stat it, return True to treat it as unwanted


def file_is_sensitive(file_path: Path) -> bool:
    return (
        file_path.suffix in PathFilters.KEY_FILE_EXTENSIONS.value
        or file_path.parts[-1] in PathFilters.KEY_FILE_NAMES.value
    )


def file_unwanted_suffix(file_path: Path) -> bool:
    return file_path.suffix in PathFilters.UNWANTED_FILE_SUFFIXES.value


def get_base_cmd(cmd: ReadCmd | WriteCmd) -> str:
    if isinstance(cmd, ReadCmd):
        return "chezmoi"
    return "chezmoi --dry-run" if store.live_run is False else "chezmoi"


def get_full_cmd(cmd: ReadCmd | WriteCmd, path: Path | None) -> str:
    path_str = str(path) if path is not None else ""
    return f"{get_base_cmd(cmd)} {' '.join(cmd.value)} {path_str}"


def get_rel_path(path: Path) -> str:
    return str(path.relative_to(store.cfg.dest_dir))


def path_seems_cache(path: Path) -> bool:
    path_parts_lower = [p.lower() for p in path.parts]
    return any(p.startswith("cache") or p.endswith("cache") for p in path_parts_lower)
