from __future__ import annotations

from itertools import islice
from typing import TYPE_CHECKING

from chezmoi_mousse import store
from chezmoi_mousse.data_types import IterDirResult, NodeData
from chezmoi_mousse.str_enums import LabelStr, PathFilters

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable
    from pathlib import Path


def sort_paths(paths: Iterable[Path]) -> list[Path]:
    path_list = list(paths)
    path_list.sort(key=lambda p: (len(p.parts), str(p).lower()))
    return path_list


def sort_path_dict[V](path_dict: dict[Path, V]) -> dict[Path, V]:
    sorted_keys = sort_paths(path_dict.keys())
    return {path: path_dict[path] for path in sorted_keys}


def any_nested_in(*, dir_path: Path, check_paths: Iterable[Path]) -> bool:
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
    if store.cfg.dest_dir_path is None or path is None or path == store.cfg.dest_dir:
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


def _get_dir_path_iterable(dir_path: Path) -> Generator[Path] | str:
    generator: Generator[Path] | None = None
    error_info: str | None = None
    try:
        if not dir_path.is_absolute():
            error_info = "Error, did not receive an absolute path"
        elif store.cfg.dest_dir not in dir_path.parents:
            error_info = (
                f"Error, got a directory which is not a child of the destDir "
                f"{store.cfg.dest_dir}"
            )
        elif dir_path.is_symlink():
            error_info = f"Error, the provided path is a symlink: {dir_path}"
        elif dir_path.is_file():
            error_info = f"Error, the provided path is a file: {dir_path}"
        else:
            generator = dir_path.iterdir()
    except (FileNotFoundError, PermissionError, OSError) as error:
        error_info = str(error)
    if error_info is not None:
        return error_info
    elif generator is not None:
        return generator
    else:
        return f"Unknown error occurred in _get_dir_path_iterable for {dir_path}"


def get_un_man_children(dir_path: Path) -> IterDirResult:
    result: Generator[Path] | str = _get_dir_path_iterable(dir_path)
    exceptions: dict[Path, str] = {}
    symlinks: list[Path] = []
    dirs: dict[Path, NodeData] = {}
    files: dict[Path, NodeData] = {}

    if not isinstance(result, str):
        for path in result:
            try:
                if path.is_symlink():
                    symlinks.append(path)
                elif path.is_dir():
                    unwanted = is_unwanted_dir(path)
                    main_label = (
                        LabelStr.un_wanted_dir if unwanted else LabelStr.un_man_dir
                    )
                    dirs[path] = NodeData(
                        dir_path=True,
                        exists=True,
                        file_path=False,
                        has_nested_status=False,
                        main_label=main_label,
                        managed_dir=False,
                        managed_file=False,
                        path=path,
                        status_dir=False,
                        status_file=False,
                        status=None,
                        un_wanted_dir=unwanted,
                        un_wanted_file=False,
                    )
                elif path.is_file():
                    is_unwanted = is_unwanted_file(path)
                    main_label = (
                        LabelStr.un_wanted_file if is_unwanted else LabelStr.un_man_file
                    )
                    files[path] = NodeData(
                        dir_path=False,
                        exists=True,
                        file_path=True,
                        has_nested_status=False,
                        main_label=main_label,
                        managed_dir=False,
                        managed_file=False,
                        path=path,
                        status_dir=False,
                        status_file=False,
                        status=None,
                        un_wanted_dir=False,
                        un_wanted_file=is_unwanted,
                    )
            except (FileNotFoundError, PermissionError, OSError) as exception:
                exceptions[path] = str(exception)

    return IterDirResult(
        error=result if isinstance(result, str) else "",
        exceptions=sort_path_dict(exceptions),
        symlinks=sort_paths(symlinks),
        dirs=sort_path_dict(dirs),
        files=sort_path_dict(files),
    )
