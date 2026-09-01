from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime
from functools import lru_cache, wraps
from itertools import islice
from pathlib import Path
from typing import TYPE_CHECKING, cast

from rich.highlighter import ReprHighlighter
from rich.text import Text

from chezmoi_mousse import store
from chezmoi_mousse.named_tuples import (
    AffectedPaths,
    CommandResult,
    DumpConfigKeys,
    ScanDirItem,
)
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
    from collections.abc import Awaitable, Callable
    from typing import Any

    from chezmoi_mousse.gui.common.operate_modal import LoadingModal


type ScanDirResult = list[ScanDirItem] | PathKind

__all__ = ["min_wait", "ParseCmd", "Commands", "CheckPath", "ScanDirResult"]

# TODO implement clearing for cached stuff upon tree or app reload

##############
# DECORATORS #
##############


def min_wait(
    func: Callable[..., Awaitable[Any]],
) -> Callable[..., Awaitable[AffectedPaths | CommandResult | None]]:
    # not needed for anything else than showing log messages briefly for humans
    @wraps(func)
    async def wrapper(self: LoadingModal, *args: Any, **kwargs: Any) -> Any:
        min_wait_time = 0.3
        start_time = time.monotonic()
        res = await func(self, *args, **kwargs)
        elapsed = time.monotonic() - start_time
        if elapsed < min_wait_time:
            await asyncio.sleep(min_wait_time - elapsed)
        return res

    return wrapper


def _typed_lru_cache[**FuncParams, FuncReturn](
    *, maxsize: int = 128, typed: bool = False
) -> Callable[[Callable[FuncParams, FuncReturn]], Callable[FuncParams, FuncReturn]]:
    def decorator(
        func: Callable[FuncParams, FuncReturn],
    ) -> Callable[FuncParams, FuncReturn]:
        return cast(
            "Callable[FuncParams, FuncReturn]",
            lru_cache(maxsize=maxsize, typed=typed)(func),
        )

    return decorator


class ParseCmd:
    @staticmethod
    @_typed_lru_cache()
    def filter_ugly_args() -> set[str]:
        ugly_args: set[str] = set()
        ugly_args.update(
            GlobalArgs.global_defaults.value,
            ChezmoiGitArgs.global_args.value,
            ChezmoiGitArgs.git_log_args.value,
            (
                VerbArgs.format_json.value,
                VerbArgs.path_style_absolute.value,
            ),
        )
        return ugly_args

    @staticmethod
    @_typed_lru_cache()
    def get_rel_path(path: Path) -> str:
        return str(path.relative_to(store.cfg.dest_dir))

    @staticmethod
    @_typed_lru_cache()
    def _cmd_str_wop(cmd: ReadCmd | WriteCmd, *, pretty: bool) -> str:
        if pretty is True:
            verb_str = " ".join(
                [a for a in cmd.value if a not in ParseCmd.filter_ugly_args()]
            )
        else:
            verb_str = " ".join(cmd.value)
        if isinstance(cmd, ReadCmd):
            base_cmd = "chezmoi"
        else:
            base_cmd = "chezmoi --dry-run" if store.live_run is False else "chezmoi"
        return f"{base_cmd} {verb_str}"

    @staticmethod
    @_typed_lru_cache()
    def pretty_cmd(cmd: ReadCmd | WriteCmd, *, path: Path | None) -> str:
        rel_path = ParseCmd.get_rel_path(path) if path is not None else ""
        return f"{ParseCmd._cmd_str_wop(cmd, pretty=True)} {rel_path}"

    @staticmethod
    @_typed_lru_cache()
    def full_cmd(cmd: ReadCmd | WriteCmd, *, path: Path | None) -> str:
        path_str = str(path) if path is not None else ""
        return f"{ParseCmd._cmd_str_wop(cmd, pretty=False)} {path_str}"

    @staticmethod
    def get_dump_config_keys(std_out: str) -> DumpConfigKeys:
        parsed_dump_config = json.loads(std_out)
        return DumpConfigKeys(
            dest_dir_path=Path(parsed_dump_config["destDir"]),
            auto_add_bool=parsed_dump_config["git"]["autoadd"],
            auto_commit_bool=parsed_dump_config["git"]["autocommit"],
            auto_push_bool=parsed_dump_config["git"]["autopush"],
        )


class Commands:
    @staticmethod
    async def _asyncio_exec(
        run_args: tuple[str, ...], time_out: int = 10
    ) -> tuple[str, str, int | None]:
        cm_exe = shutil.which(run_args[0])
        if cm_exe is None:
            raise RuntimeError("chezmoi executable not found in PATH")

        process = await asyncio.create_subprocess_exec(
            cm_exe,
            *run_args[1:],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            async with asyncio.timeout(time_out):
                stdout_bytes, stderr_bytes = await process.communicate()
        except TimeoutError as e:
            process.kill()
            await process.wait()
            raise subprocess.TimeoutExpired(
                cmd=run_args,
                timeout=time_out,
            ) from e

        std_out = (stdout_bytes or b"").decode("utf-8", errors="replace").strip("\r\n")
        std_err = (stderr_bytes or b"").decode("utf-8", errors="replace").strip("\r\n")

        return std_out, std_err, process.returncode

    @staticmethod
    async def _get_exec_result(
        args_tuple: tuple[str, ...],
        *,
        path: Path | None,
        cmd_enum: ReadCmd | WriteCmd,
    ) -> CommandResult:

        if path is None:
            run_args = args_tuple
        elif not path.is_absolute():
            raise ValueError("Calling subprocess with a relative path")
        else:
            run_args = args_tuple + (str(path),)

        std_out, std_err, result_code = await Commands._asyncio_exec(run_args)

        if not std_out and not std_err:
            out_lines: list[str] = []
            out_lines.append("Output on stdout:")
            out_lines.append(std_out)
            out_lines.append("Output on stderr:")
            out_lines.append(std_err)
            out_txt = "\n\n".join(out_lines)
        elif not std_out and std_err:
            out_txt = std_err
        elif std_out and not std_err:
            out_txt = std_out
        else:
            out_txt = f"Output on stdout:\n{std_out}\n\nOutput on stderr:\n{std_err}"

        return CommandResult(
            cmd_enum=cmd_enum,
            full_cmd=f"{ParseCmd.full_cmd(cmd_enum, path=path)}",
            out_txt=out_txt,
            path_arg=path,
            pretty_cmd=f"{ParseCmd.pretty_cmd(cmd_enum, path=path)}",
            returncode=result_code,
            std_err=std_err,
            std_out=std_out,
            time_stamp=f"{datetime.now().strftime('%H:%M:%S')}",
        )

    @staticmethod
    def _subprocess_get_affected_paths(
        args_tuple: tuple[str, ...],
    ) -> tuple[set[str], str, int]:

        affected_paths_str: set[str] = set()
        path_pattern = re.compile(r"^diff --git a/.* b/(.*)$")

        # Launch process
        with subprocess.Popen(
            args_tuple,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
        ) as process:
            # Stream stdout line-by-line
            if process.stdout is not None:
                for line in process.stdout:
                    match = path_pattern.match(line)
                    if match:
                        affected_paths_str.add(match.group(1))

            # Read any remaining stderr output after stdout completes
            stderr_output = process.stderr.read() if process.stderr is not None else ""

            returncode = process.wait()
            return affected_paths_str, stderr_output, returncode

    @staticmethod
    async def get_affected_paths(write_cmd: WriteCmd, path: Path) -> AffectedPaths:
        path_arg: tuple[str, ...] = (str(path),)
        # Only works for apply and re-add, not for add, forget and destroy
        if path == store.cfg.dest_dir and write_cmd in (
            WriteCmd.add,
            WriteCmd.destroy,
            WriteCmd.forget,
        ):
            # TODO: disable the chezmoi review button, so it should never happen
            raise ValueError(f"Cannot run chezmoi on the destDir for {write_cmd.name}")
        path_arg = () if path == store.cfg.dest_dir else (str(path),)

        # Build command arguments
        args_tuple: tuple[str, ...] = (
            ("chezmoi",)
            + GlobalArgs.global_defaults.value
            + (
                GlobalArgs.verbose.value,
                GlobalArgs.dry_run.value,
            )
            + write_cmd.value
            + path_arg
        )

        rel_path = ParseCmd.get_rel_path(path) if path != store.cfg.dest_dir else ""
        pretty_cmd = " ".join(
            [a for a in args_tuple if a not in ParseCmd.filter_ugly_args()]
        )

        # Offload the blocking streaming execution to a thread worker
        affected_paths_str, stderr_output, returncode = await asyncio.to_thread(
            Commands._subprocess_get_affected_paths, args_tuple
        )
        return AffectedPaths(
            paths=sorted([Path(path_str) for path_str in affected_paths_str]),
            pretty_cmd=f"{pretty_cmd} {rel_path}",
            std_err=stderr_output,
            returncode=returncode,
        )

    @staticmethod
    async def exec_read_cmd(cmd: ReadCmd, path_arg: Path | None) -> CommandResult:
        args_tuple: tuple[str, ...] = ("chezmoi",) + cmd.value
        cmd_result: CommandResult = await Commands._get_exec_result(
            args_tuple, path=path_arg, cmd_enum=cmd
        )
        return cmd_result

    @staticmethod
    async def run_chezmoi_init() -> CommandResult:
        cmd_result: CommandResult = await Commands._get_exec_result(
            ("chezmoi",), path=None, cmd_enum=WriteCmd.init
        )
        return cmd_result

    @staticmethod
    async def run_write_cmd(cmd: WriteCmd, path_arg: Path | None) -> CommandResult:
        args_tuple: tuple[str, ...] = (
            ("chezmoi", "--dry-run") + cmd.value
            if store.live_run is False
            else ("chezmoi",) + cmd.value
        )
        cmd_result: CommandResult = await Commands._get_exec_result(
            args_tuple, path=path_arg, cmd_enum=cmd
        )
        return cmd_result

    @staticmethod
    @_typed_lru_cache(maxsize=500)
    def get_highlighted_file_contents(file_path: Path) -> Text:
        if file_path.is_dir():
            raise ValueError(
                f"Trying to get file contents for a directory: {file_path}"
            )
        try:
            max_chars = 500000
            with file_path.open("r", encoding="utf-8") as f:
                # Over-read by 1 char to test truncation in 1 I/O btn_label
                data = f.read(max_chars + 1)
            truncated = len(data) > max_chars
            f_contents = data[:max_chars]
            if not f_contents.strip():
                f_contents = "File is empty or contains only whitespace"
            elif truncated:
                f_contents += f"\n--- Read file limited to {max_chars} characters ---"
        except (PermissionError, OSError, UnicodeDecodeError) as e:
            f_contents = str(e)
        text_contents = Text(f_contents)
        ReprHighlighter().highlight(text_contents)
        return text_contents

    @staticmethod
    async def get_highlighted_chezmoi_cat_output(
        file_path: Path,
    ) -> Text:
        cmd_result = await Commands.exec_read_cmd(ReadCmd.cat, path_arg=file_path)
        f_contents = cmd_result.std_out
        if not f_contents.strip():
            f_contents = "File is empty or contains only whitespace"
        text_contents = Text(f_contents)
        ReprHighlighter().highlight(text_contents)
        return text_contents

    @staticmethod
    async def _get_source_path(path_arg: Path) -> CommandResult:
        return await Commands.exec_read_cmd(ReadCmd.source_path, path_arg=path_arg)

    @staticmethod
    @_typed_lru_cache()
    def parse_git_log_result(cmd_result: CommandResult) -> list[tuple[str, str]]:
        parsed_rows: list[tuple[str, str]] = []
        no_commit_message = "no commit message"

        for line in cmd_result.std_out.splitlines():
            rel_date, committer, subject = line.rstrip().split("\x1f", 2)
            col_one = f"{rel_date} by {committer}"
            col_two = subject if subject.strip() else no_commit_message
            parsed_rows.append((col_one, col_two))
        return parsed_rows

    @staticmethod
    async def run_chezmoi_git_log(path_arg: Path) -> CommandResult:
        if path_arg == store.cfg.dest_dir:
            result = await Commands.exec_read_cmd(ReadCmd.git_log, path_arg=None)
        else:
            source_path_result = await Commands._get_source_path(path_arg)
            if source_path_result.returncode != 0:
                return source_path_result
            result = await Commands.exec_read_cmd(
                cmd=ReadCmd.git_log,
                path_arg=Path(source_path_result.std_out),
            )
        return result

    @staticmethod
    async def run_chezmoi_diff(diff_cmd: ReadCmd, path: Path) -> CommandResult:
        return await Commands.exec_read_cmd(diff_cmd, path_arg=path)


class CheckPath:
    @staticmethod
    @_typed_lru_cache(maxsize=1000)
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
    @_typed_lru_cache(maxsize=4000)
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
    @_typed_lru_cache(maxsize=4000)
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
    @_typed_lru_cache(maxsize=4000)
    def is_unwanted_dir(dir_path: Path) -> bool:
        return (
            CheckPath._looks_like_cache(dir_path)
            or CheckPath._is_unwanted_dir_name(dir_path)
            or CheckPath._is_git_objects_dir(dir_path)
            or CheckPath._dir_has_many_children(dir_path)
        )
