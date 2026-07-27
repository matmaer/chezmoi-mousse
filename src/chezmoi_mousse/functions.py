from __future__ import annotations

import subprocess
from datetime import datetime
from itertools import islice
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse.cm_command import ReadCmd, WriteCmd
from chezmoi_mousse.cm_types import CommandResult, typed_lru_cache
from chezmoi_mousse.str_enums import ChezmoiGitArgs, GlobalArgs, PathFilters, VerbArgs

if TYPE_CHECKING:
    from chezmoi_mousse.cm_types import StrTup

__all__ = ("run_chezmoi_cmd", "CheckPath")


def get_ugly_args() -> set[str]:
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


@typed_lru_cache()
def _ugly_args() -> set[str]:
    return get_ugly_args()


@typed_lru_cache()
def _args_without_path(*, cmd: ReadCmd | WriteCmd, dry: bool) -> StrTup:
    return (
        ("chezmoi",) + cmd.value
        if dry is False
        else ("chezmoi", "--dry-run") + cmd.value
    )


@typed_lru_cache()
def _cmd_str_without_path(*, cmd: ReadCmd | WriteCmd, dry: bool, pretty: bool) -> str:
    verb_str = (
        " ".join(cmd.value)
        if pretty is False
        else " ".join([a for a in cmd.value if a not in _ugly_args()])
    )
    return f"chezmoi {verb_str}" if dry is False else f"chezmoi --dry-run {verb_str}"


@typed_lru_cache()
def _pretty_cmd(*, base_str: str, path_arg: Path | None) -> str:
    return base_str if path_arg is None else f"{base_str} {path_arg}"


def _subprocess_run(
    *, args: StrTup, path: Path | None, time_out: int
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


def run_chezmoi_cmd(
    command: ReadCmd | WriteCmd, *, dry_run: bool, path_arg: Path | None = None
) -> CommandResult:

    args: StrTup = _args_without_path(cmd=command, dry=dry_run)
    time_out: int = 10 if isinstance(command, ReadCmd) else 20
    cp: subprocess.CompletedProcess[str] = _subprocess_run(
        args=args, path=path_arg, time_out=time_out
    )
    out_lines = [line for line in cp.stdout.splitlines() if line.strip()]
    std_out = "\n".join(out_lines)

    err_lines = [line for line in cp.stderr.splitlines() if line.strip()]
    std_err = "\n".join(err_lines)

    full_cmd_str = (
        f"{_cmd_str_without_path(cmd=command, dry=dry_run, pretty=True)} {path_arg}"
    )
    pretty_cmd_str_wop = _cmd_str_without_path(cmd=command, dry=dry_run, pretty=True)
    pretty_cmd = _pretty_cmd(base_str=pretty_cmd_str_wop, path_arg=path_arg)

    return CommandResult(
        dry_run=dry_run,
        err_lines=err_lines,
        full_cmd_str=full_cmd_str,
        out_lines=out_lines,
        pretty_cmd=pretty_cmd,
        path_arg=path_arg,
        returncode=cp.returncode,
        std_err=std_err,
        std_out=std_out,
        time_stamp=f"{datetime.now().strftime('%H:%M:%S')}",
    )


class CheckPath:

    # functions for file paths

    @staticmethod
    def is_sensitive(file_path: Path) -> bool:
        return (
            file_path.suffix in PathFilters.KEY_FILE_EXTENSIONS.value
            or file_path.parts[-1] in PathFilters.KEY_FILE_NAMES.value
        )

    @staticmethod
    @typed_lru_cache(maxsize=4000)
    def is_large(file_path: Path) -> bool:
        # check if it's a large file, typically not a dot file
        return file_path.stat().st_size > 1024 * 1024  # 1 MiB

    @staticmethod
    @typed_lru_cache(maxsize=4000)
    def is_binary(file_path: Path) -> bool:
        # check if the file looks like a binary
        try:
            with Path.open(file_path, "rb") as f:
                chunk = f.read(1024)  # Read only first KiB
            return b"\x00" in chunk  # typically the case for binary files
        except OSError:
            return True

    @staticmethod
    def is_bad_suffix(file_path: Path) -> bool:
        return file_path.suffix in PathFilters.UNWANTED_FILE_SUFFIXES.value

    # functions for dir paths

    @staticmethod
    def is_unwanted_dir_name(dir_path: Path) -> bool:
        return dir_path.parts[-1] in PathFilters.UNWANTED_DIRS.value

    @staticmethod
    def is_git_objects_dir(dir_path: Path) -> bool:
        return dir_path.parts[-1] == "objects" and dir_path.parts[-2] == ".git"

    @staticmethod
    @typed_lru_cache(maxsize=4000)
    def has_many_children(dir_path: Path, max_entries: int = 200) -> bool:
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
    def get_unchanged_dir_paths_in(
        dir_path: Path, managed_files: set[Path]
    ) -> list[Path]:
        results: set[Path] = set()
        for path in managed_files:
            if path != dir_path and path.is_relative_to(dir_path):
                results.add(path)
        return sorted(results)

    @staticmethod
    @typed_lru_cache(maxsize=4000)
    def get_unchanged_file_paths_in(
        dir_path: Path, managed_dirs: dict[Path, str]
    ) -> list[Path]:
        results: set[Path] = set()
        for path in managed_dirs:
            if path.is_relative_to(dir_path):
                results.add(path)
        return sorted(results)

    # functions for both file and dir paths

    @staticmethod
    @typed_lru_cache(maxsize=4000)
    def looks_like_cache(path: Path) -> bool:
        path_parts_lower = [p.lower() for p in path.parts]
        return any(
            p.startswith("cache") or p.endswith("cache") for p in path_parts_lower
        )

    @staticmethod
    def clear_caches() -> None:
        for attr_name in dir(CheckPath):
            attr = getattr(CheckPath, attr_name)
            if hasattr(attr, "cache_clear"):
                attr.cache_clear()
