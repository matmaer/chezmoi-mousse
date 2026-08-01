from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from itertools import islice
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse.cm_command import ReadCmd, WriteCmd
from chezmoi_mousse.cm_types import CommandResult, ScanDirItem, typed_lru_cache
from chezmoi_mousse.str_enums import (
    ChezmoiGitArgs,
    GlobalArgs,
    PathFilters,
    PathKind,
    VerbArgs,
)

if TYPE_CHECKING:
    from chezmoi_mousse.cm_types import ParsedJson, StrTuple

__all__ = ("Commands", "CheckPath")

# TODO implement clearing for cached stuff in other classes than AppLife


class AppLife:
    """Contains caches never to be cleared during the application its life."""

    @staticmethod
    @typed_lru_cache()
    def _ugly_args() -> set[str]:
        ugly_args: set[str] = set()
        ugly_args.update(
            GlobalArgs.global_defaults.value,
            ChezmoiGitArgs.global_args.value,
            ChezmoiGitArgs.git_log_args.value,
            (
                ChezmoiGitArgs.verbose.value,
                VerbArgs.format_json.value,
                VerbArgs.path_style_absolute.value,
            ),
        )
        return ugly_args

    @staticmethod
    @typed_lru_cache()
    def cmd_str_wop(cmd: ReadCmd | WriteCmd, *, dry: bool | None, pretty: bool) -> str:
        verb_str = (
            " ".join(cmd.value)
            if pretty is False
            else " ".join([a for a in cmd.value if a not in AppLife._ugly_args()])
        )
        if isinstance(cmd, ReadCmd) and dry is None:
            return f"chezmoi {verb_str}"
        elif isinstance(cmd, WriteCmd) and dry is not None:
            return (
                f"chezmoi {verb_str}"
                if dry is False
                else f"chezmoi --dry-run {verb_str}"
            )
        else:
            raise ValueError(f"Received invalid params for {cmd}, dry={dry}")

    @staticmethod
    @typed_lru_cache(maxsize=500)
    def parents(path: Path, stop_path: Path) -> tuple[Path, ...]:

        std_parents = path.parents
        if path == stop_path or stop_path not in std_parents:
            raise RuntimeError(
                f"Path '{path}' is not a child of stop_path '{stop_path}'"
            )
        return tuple(std_parents[: std_parents.index(stop_path)])


class Commands:

    def _subprocess_run(
        *, args: StrTuple, path: Path | None, time_out: int
    ) -> subprocess.CompletedProcess[str]:
        if path is None:
            run_args = args
        elif not path.is_absolute():
            raise ValueError("Calling subprocess.run with a relative path")
        else:
            run_args = args + (str(path),)
        return subprocess.run(
            run_args, capture_output=True, shell=False, text=True, timeout=time_out
        )

    @staticmethod
    def run_read_cmd(cmd: ReadCmd, path_arg: Path | None = None) -> CommandResult:
        args: StrTuple = ("chezmoi",) + cmd.value
        cp: subprocess.CompletedProcess[str] = Commands._subprocess_run(
            args=args, path=path_arg, time_out=5
        )
        out_lines = [line for line in cp.stdout.splitlines() if line.strip()]
        std_out = "\n".join(out_lines)

        err_lines = [line for line in cp.stderr.splitlines() if line.strip()]
        std_err = "\n".join(err_lines)

        full_cmd_str = f"{AppLife.cmd_str_wop(cmd, dry=None, pretty=True)} {path_arg}"
        pretty_read_cmd_wop = AppLife.cmd_str_wop(cmd=cmd, dry=None, pretty=True)
        pretty_read_cmd = (
            pretty_read_cmd_wop
            if path_arg is None
            else f"{pretty_read_cmd_wop} {path_arg})"
        )

        return CommandResult(
            dry_run=None,
            err_lines=err_lines,
            full_cmd_str=full_cmd_str,
            out_lines=out_lines,
            pretty_cmd=pretty_read_cmd,
            path_arg=path_arg,
            returncode=cp.returncode,
            std_err=std_err,
            std_out=std_out,
            time_stamp=f"{datetime.now().strftime('%H:%M:%S')}",
        )

    @staticmethod
    def run_write_cmd(
        cmd: WriteCmd, dry_run: bool, path_arg: Path | None = None
    ) -> CommandResult:
        args: StrTuple = (
            ("chezmoi",) + cmd.value
            if dry_run is True
            else ("chezmoi", "--dry-run") + cmd.value
        )
        cp: subprocess.CompletedProcess[str] = Commands._subprocess_run(
            args=args, path=path_arg, time_out=20
        )
        out_lines = [line for line in cp.stdout.splitlines() if line.strip()]
        std_out = "\n".join(out_lines)

        err_lines = [line for line in cp.stderr.splitlines() if line.strip()]
        std_err = "\n".join(err_lines)

        full_cmd_str = (
            f"{AppLife.cmd_str_wop(cmd, dry=dry_run, pretty=True)} {path_arg}"
        )
        pretty_write_cmd_wop = AppLife.cmd_str_wop(cmd=cmd, dry=dry_run, pretty=True)
        pretty_write_cmd = (
            pretty_write_cmd_wop
            if path_arg is None
            else f"{pretty_write_cmd_wop} {path_arg})"
        )

        return CommandResult(
            dry_run=dry_run,
            err_lines=err_lines,
            full_cmd_str=full_cmd_str,
            out_lines=out_lines,
            pretty_cmd=pretty_write_cmd,
            path_arg=path_arg,
            returncode=cp.returncode,
            std_err=std_err,
            std_out=std_out,
            time_stamp=f"{datetime.now().strftime('%H:%M:%S')}",
        )

    @staticmethod
    def json_loads(str_to_parse: str) -> ParsedJson:
        return json.loads(str_to_parse)

    @staticmethod
    @typed_lru_cache(maxsize=500)
    def run_chezmoi_git_log(path_arg: Path | None = None) -> CommandResult:
        if path_arg is None:
            return Commands.run_read_cmd(ReadCmd.git_log, path_arg=path_arg)
        else:
            source_path_result = Commands.run_read_cmd(
                cmd=ReadCmd.source_path, path_arg=path_arg
            )
            return Commands.run_read_cmd(
                cmd=ReadCmd.git_log, path_arg=Path(source_path_result.std_out)
            )


class CheckPath:

    @staticmethod
    @typed_lru_cache(maxsize=1000)
    def os_scan_dir(
        dir_path: Path, managed_dir: bool = False
    ) -> list[ScanDirItem] | PathKind:
        scan_dir_items: list[ScanDirItem] = []
        # str(dir_path) to reduce possible exceptions which would be raised by pathlib
        try:
            with os.scandir(str(dir_path)) as entry_generator:
                dir_entries: list[os.DirEntry[str]] = list(entry_generator)
        except FileNotFoundError as dir_path_not_found:
            if managed_dir:
                return PathKind.man_dir_not_exists
            else:
                raise dir_path_not_found  # fail fast
        except PermissionError:
            if managed_dir:
                return PathKind.man_dir_access_denied
            else:
                # can happen in ManagedTree scan
                return PathKind.unman_dir_access_denied

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
                matches_unwanted = CheckPath.is_unwanted_dir(de_path)
            elif is_file:
                try:
                    file_size = de.stat().st_size
                except OSError:
                    file_size = None
                    matches_unwanted = True
                else:
                    matches_unwanted = CheckPath.is_unwanted_file(de_path)
            else:
                matches_unwanted = True

            scan_dir_items.append(
                ScanDirItem(
                    scanned_dir=dir_path,
                    managed_arg=managed_dir,
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

    # functions for both file and dir paths

    @staticmethod
    def _looks_like_cache(path: Path) -> bool:
        path_parts_lower = [p.lower() for p in path.parts]
        return any(
            p.startswith("cache") or p.endswith("cache") for p in path_parts_lower
        )

    # functions for file paths

    @staticmethod
    @typed_lru_cache(maxsize=4000)
    def _is_sensitive(file_path: Path) -> bool:
        return (
            file_path.suffix in PathFilters.KEY_FILE_EXTENSIONS.value
            or file_path.parts[-1] in PathFilters.KEY_FILE_NAMES.value
        )

    @staticmethod
    def _is_large(file_path: Path) -> bool:
        # check if it's a large file, typically not a dot file
        return file_path.stat().st_size > 1024 * 1024  # 1 MiB

    @staticmethod
    def _is_binary(file_path: Path) -> bool:
        # check if the file looks like a binary
        try:
            with Path.open(file_path, "rb") as f:
                chunk = f.read(1024)  # Read only first KiB
            return b"\x00" in chunk  # typically the case for binary files
        except OSError:
            return True

    @staticmethod
    def _is_bad_suffix(file_path: Path) -> bool:
        return file_path.suffix in PathFilters.UNWANTED_FILE_SUFFIXES.value

    @staticmethod
    @typed_lru_cache(maxsize=4000)
    def is_unwanted_file(file_path: Path) -> bool:
        return (
            CheckPath._looks_like_cache(file_path)
            or CheckPath._is_sensitive(file_path)
            or CheckPath._is_bad_suffix(file_path)
            or CheckPath._is_large(file_path)
            or CheckPath._is_binary(file_path)
        )

    # functions for dir paths

    @staticmethod
    def _is_unwanted_dir_name(dir_path: Path) -> bool:
        return dir_path.parts[-1] in PathFilters.UNWANTED_DIRS.value

    @staticmethod
    def _is_git_objects_dir(dir_path: Path) -> bool:
        return dir_path.parts[-1] == "objects" and dir_path.parts[-2] == ".git"

    @staticmethod
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

    @staticmethod
    @typed_lru_cache(maxsize=4000)
    def is_unwanted_dir(dir_path: Path) -> bool:
        return (
            CheckPath._looks_like_cache(dir_path)
            or CheckPath._is_unwanted_dir_name(dir_path)
            or CheckPath._is_git_objects_dir(dir_path)
            or CheckPath._dir_has_many_children(dir_path)
        )

    # used by ManagedTree

    @staticmethod
    @typed_lru_cache(maxsize=500)
    def tree_status_dirs_in(
        dir_path: Path, tree_status_dirs: frozenset[Path]
    ) -> frozenset[Path]:
        return frozenset(path for path in tree_status_dirs if path.parent == dir_path)

    @staticmethod
    @typed_lru_cache(maxsize=500)
    def status_files_in(
        dir_path: Path, status_files: frozenset[Path]
    ) -> frozenset[Path]:
        return frozenset(path for path in status_files if path.parent == dir_path)

    @staticmethod
    @typed_lru_cache(maxsize=500)
    def unchanged_paths_in(
        dir_path: Path, unchanged: frozenset[Path]
    ) -> frozenset[Path]:
        return frozenset(path for path in unchanged if path.parent == dir_path)
