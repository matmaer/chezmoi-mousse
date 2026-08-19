from __future__ import annotations

import json
import os
import subprocess
import time
from asyncio import sleep
from collections.abc import Callable
from datetime import datetime
from functools import lru_cache, wraps
from itertools import islice
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, cast

from rich.highlighter import ReprHighlighter
from rich.text import Text

from chezmoi_mousse.named_tuples import CommandResult, ScanDirItem
from chezmoi_mousse.str_enums import (
    ChezmoiGitArgs,
    GlobalArgs,
    PathFilters,
    PathKind,
    ReadCmd,
    VerbArgs,
    WriteCmd,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from chezmoi_mousse.cm_types import (
        MinWaitReturn,
        ParsedJson,
        ScanDirResult,
        StrTuple,
    )
    from chezmoi_mousse.gui.common.actionables import ReviewButton
    from chezmoi_mousse.gui.common.loading_modal import LoadingModal

__all__ = ("min_wait", "AppLife", "Commands", "CheckPath", "ResultCollector")


def min_wait(func: Callable[..., Awaitable[None]]) -> MinWaitReturn:
    # not needed for anything else than showing log messages briefly for humans
    @wraps(func)
    async def wrapper(self: LoadingModal, *args: ReviewButton) -> None:
        min_wait_time = 0.2
        start_time = time.monotonic()
        await func(self, *args)
        elapsed = time.monotonic() - start_time
        if elapsed < min_wait_time:
            await sleep(min_wait_time - elapsed)

    return wrapper


def typed_lru_cache[**FuncParams, FuncReturn](
    *, maxsize: int = 128, typed: bool = False
) -> Callable[[Callable[FuncParams, FuncReturn]], Callable[FuncParams, FuncReturn]]:
    def decorator(
        func: Callable[FuncParams, FuncReturn],
    ) -> Callable[FuncParams, FuncReturn]:
        return cast(
            Callable[FuncParams, FuncReturn],
            lru_cache(maxsize=maxsize, typed=typed)(func),
        )

    return decorator


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

        if isinstance(cmd, ReadCmd):
            if dry is not None:
                raise ValueError(f"Read commands are always live; received dry={dry}")
            return f"chezmoi {verb_str}"

        if dry is None:
            raise ValueError(f"Write commands require dry flag; received dry={dry}")
        return f"chezmoi --dry-run {verb_str}" if dry is True else f"chezmoi {verb_str}"

    @staticmethod
    @typed_lru_cache()
    def strip_empty_lines(text: str) -> str:
        return "\n".join([line for line in text.splitlines() if line.strip()])


class ResultCollector:
    # chezmoi ReadCmd results which do not require arguments or which require the path
    # arg to be None if ran on the dest dir, eg git_log
    cat_config_result: ClassVar[CommandResult]
    doctor_result: ClassVar[CommandResult]
    dump_config_result: ClassVar[CommandResult]
    git_remote_result: ClassVar[CommandResult]
    ignored_result: ClassVar[CommandResult]
    managed_dirs_result: ClassVar[CommandResult]
    managed_files_result: ClassVar[CommandResult]
    status_dirs_result: ClassVar[CommandResult]
    status_files_result: ClassVar[CommandResult]
    template_data_result: ClassVar[CommandResult]

    # Processed json results in SplashScreen
    parsed_dump_config: ParsedJson
    parsed_template_data: ParsedJson

    # Used for logging after the splash screen is disimissed and we push the MainScreen
    @classmethod
    def splash_results(cls) -> list[CommandResult]:
        return [
            cls.cat_config_result,
            cls.doctor_result,
            cls.dump_config_result,
            cls.git_remote_result,
            cls.ignored_result,
            cls.managed_dirs_result,
            cls.managed_files_result,
            cls.status_dirs_result,
            cls.status_files_result,
            cls.template_data_result,
        ]

    # Used to retrieve results after the 'Refresh Tree' button was clicked
    @classmethod
    def managed_cmd_results(cls) -> list[CommandResult]:
        return [
            cls.managed_dirs_result,
            cls.managed_files_result,
            cls.status_dirs_result,
            cls.status_files_result,
        ]

    @classmethod
    def get_dest_dir(cls) -> Path:
        return Path(ResultCollector.parsed_dump_config["destDir"])


class Commands:
    @staticmethod
    def _subprocess_run(
        args_tuple: StrTuple, *, path: Path | None, time_out: int
    ) -> subprocess.CompletedProcess[str]:
        if path is None:
            run_args = args_tuple
        elif not path.is_absolute():
            raise ValueError("Calling subprocess.run with a relative path")
        else:
            run_args = args_tuple + (str(path),)
        return subprocess.run(
            run_args, capture_output=True, shell=False, text=True, timeout=time_out
        )

    @staticmethod
    def run_read_cmd(cmd: ReadCmd, path_arg: Path | None = None) -> CommandResult:
        args_tuple: StrTuple = ("chezmoi",) + cmd.value
        cp: subprocess.CompletedProcess[str] = Commands._subprocess_run(
            args_tuple, path=path_arg, time_out=5
        )

        full_cmd_str = f"{AppLife.cmd_str_wop(cmd, dry=None, pretty=True)} {path_arg}"
        pretty_read_cmd_wop = AppLife.cmd_str_wop(cmd=cmd, dry=None, pretty=True)
        pretty_read_cmd = (
            pretty_read_cmd_wop
            if path_arg is None
            else f"{pretty_read_cmd_wop} {path_arg})"
        )

        result = CommandResult(
            dry_run=None,
            full_cmd_str=full_cmd_str,
            pretty_cmd=pretty_read_cmd,
            path_arg=path_arg,
            returncode=cp.returncode,
            std_err=AppLife.strip_empty_lines(cp.stderr),
            std_out=AppLife.strip_empty_lines(cp.stdout),
            time_stamp=f"{datetime.now().strftime('%H:%M:%S')}",
        )
        if path_arg is None:
            setattr(ResultCollector, f"{cmd.name}_result", result)
        return result

    @staticmethod
    def run_write_cmd(
        cmd: WriteCmd, dry_run: bool, path_arg: Path | None = None
    ) -> CommandResult:
        args_tuple: StrTuple = (
            ("chezmoi", "--dry-run") + cmd.value
            if dry_run is True
            else ("chezmoi",) + cmd.value
        )
        cp: subprocess.CompletedProcess[str] = Commands._subprocess_run(
            args_tuple, path=path_arg, time_out=20
        )
        full_cmd_str = (
            f"{AppLife.cmd_str_wop(cmd, dry=dry_run, pretty=True)} {path_arg}"
        )
        pretty_write_cmd_wop = AppLife.cmd_str_wop(cmd=cmd, dry=dry_run, pretty=True)
        pretty_write_cmd = (
            pretty_write_cmd_wop
            if path_arg is None
            else f"{pretty_write_cmd_wop} {path_arg})"
        )

        result = CommandResult(
            dry_run=dry_run,
            full_cmd_str=full_cmd_str,
            pretty_cmd=pretty_write_cmd,
            path_arg=path_arg,
            returncode=cp.returncode,
            std_err=AppLife.strip_empty_lines(cp.stderr),
            std_out=AppLife.strip_empty_lines(cp.stdout),
            time_stamp=f"{datetime.now().strftime('%H:%M:%S')}",
        )
        setattr(ResultCollector, cmd.name, result)
        return result

    @staticmethod
    def json_loads(str_to_parse: str) -> ParsedJson:
        return json.loads(str_to_parse)

    @staticmethod
    @typed_lru_cache(maxsize=500)
    def get_highlighted_file_contents(file_path: Path) -> Text:
        if file_path.is_dir():
            raise ValueError(
                f"Trying to get file contents for a directory: {file_path}"
            )
        try:
            max_chars = 500000
            with file_path.open("r", encoding="utf-8") as f:
                # Over-read by 1 char to test truncation in 1 I/O operation
                data = f.read(max_chars + 1)
            truncated = len(data) > max_chars
            f_contents = data[:max_chars]
            if not f_contents.strip():
                f_contents = "File is empty or contains only whitespace"
            elif truncated:
                f_contents += f"\n--- Read file limited to {max_chars} characters ---"
        except (PermissionError, OSError, UnicodeDecodeError) as e:
            f_contents = str(e)
        f_contents = Text(f_contents)
        ReprHighlighter().highlight(f_contents)
        return f_contents

    @staticmethod
    @typed_lru_cache(maxsize=500)
    def get_highlighted_chezmoi_cat_output(
        file_path: Path,
    ) -> tuple[Text, CommandResult]:
        cmd_result = Commands.run_read_cmd(cmd=ReadCmd.cat, path_arg=file_path)
        f_contents = cmd_result.std_out
        if not f_contents.strip():
            f_contents = "File is empty or contains only whitespace"
        f_contents = Text(f_contents)
        ReprHighlighter().highlight(f_contents)
        return (f_contents, cmd_result)

    @staticmethod
    @typed_lru_cache(maxsize=500)
    def run_chezmoi_git_log(path_arg: Path | None) -> CommandResult:
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
    def os_scan_dir(dir_path: Path, *, managed_dir: bool = False) -> ScanDirResult:

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

            if matches_unwanted and managed_dir:
                continue

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
        try:
            return file_path.stat().st_size > 512 * 1024  # half a megabyte
        except OSError:
            return True  # if we can't stat it, return True to treat it as unwanted

    @staticmethod
    def _is_binary(file_path: Path) -> bool:
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
