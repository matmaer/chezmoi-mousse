from __future__ import annotations

import json
import os
from datetime import datetime
from itertools import islice
from pathlib import Path
from typing import TYPE_CHECKING

from rich.highlighter import ReprHighlighter
from rich.text import Text

from chezmoi_mousse import store
from chezmoi_mousse.asyncio_process_exec import (
    execute_chezmoi_command,
    get_affected_paths,
)
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
    from chezmoi_mousse.asyncio_process_exec import (
        ExecResult,
    )

type ScanDirResult = list[ScanDirItem] | PathKind

__all__ = ["CheckPath", "Commands", "ScanDirResult"]


class _ParseCmd:
    @staticmethod
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
    def get_rel_path(path: Path) -> str:
        return str(path.relative_to(store.cfg.dest_dir))

    @staticmethod
    def _cmd_str_wop(cmd: ReadCmd | WriteCmd, *, pretty: bool) -> str:
        if pretty is True:
            verb_str = " ".join(
                [a for a in cmd.value if a not in _ParseCmd.filter_ugly_args()]
            )
        else:
            verb_str = " ".join(cmd.value)
        if isinstance(cmd, ReadCmd):
            base_cmd = "chezmoi"
        else:
            base_cmd = "chezmoi --dry-run" if store.live_run is False else "chezmoi"
        return f"{base_cmd} {verb_str}"

    @staticmethod
    def pretty_cmd(cmd: ReadCmd | WriteCmd, path: Path | None) -> str:
        rel_path = _ParseCmd.get_rel_path(path) if path is not None else ""
        return f"{_ParseCmd._cmd_str_wop(cmd, pretty=True)} {rel_path}"

    @staticmethod
    def full_cmd(cmd: ReadCmd | WriteCmd, path: Path | None) -> str:
        path_str = str(path) if path is not None else ""
        return f"{_ParseCmd._cmd_str_wop(cmd, pretty=False)} {path_str}"

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
    async def exec_chezmoi_cmd(
        cmd_enum: ReadCmd | WriteCmd,
        path_arg: Path | None,
    ) -> CommandResult:

        exec_result: ExecResult = await execute_chezmoi_command(cmd_enum, path_arg)

        std_out = exec_result[0]
        std_err = exec_result[1]
        result_code = exec_result[2]
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
            full_cmd=f"{_ParseCmd.full_cmd(cmd_enum, path_arg)}",
            out_txt=out_txt,
            path_arg=path_arg,
            pretty_cmd=f"{_ParseCmd.pretty_cmd(cmd_enum, path_arg)}",
            returncode=result_code,
            std_err=std_err,
            std_out=std_out,
            time_stamp=f"{datetime.now().strftime('%H:%M:%S')}",
        )

    @staticmethod
    async def get_affected_paths(write_cmd: WriteCmd, path: Path) -> AffectedPaths:
        # Only works for apply and re-add, not for add, forget and destroy
        if path == store.cfg.dest_dir and write_cmd in (
            WriteCmd.add,
            WriteCmd.destroy,
            WriteCmd.forget,
        ):
            # TODO: disable the chezmoi review button, so it should never happen
            raise ValueError(f"Cannot run chezmoi on the destDir for {write_cmd.name}")
        path_arg = "" if path == store.cfg.dest_dir else str(path)

        # Build command arguments
        args_tuple: tuple[str, ...] = (
            "chezmoi",
            *GlobalArgs.global_defaults.value,
            GlobalArgs.verbose.value,
            GlobalArgs.dry_run.value,
            *write_cmd.value,
            path_arg,
        )

        rel_path = _ParseCmd.get_rel_path(path) if path != store.cfg.dest_dir else ""
        pretty_cmd = " ".join(
            [a for a in args_tuple if a not in _ParseCmd.filter_ugly_args()]
        )

        # Offload the blocking streaming execution to a thread worker
        std_out, std_err, returncode = await get_affected_paths(
            verb=write_cmd.value[0], path=path_arg
        )
        return AffectedPaths(
            paths=sorted([Path(path_str) for path_str in std_out.splitlines()]),
            pretty_cmd=f"{pretty_cmd} {rel_path}",
            std_err=std_err,
            returncode=returncode,
        )

    @staticmethod
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
        cmd_result = await Commands.exec_chezmoi_cmd(ReadCmd.cat, file_path)
        f_contents = cmd_result.std_out
        if not f_contents.strip():
            f_contents = "File is empty or contains only whitespace"
        text_contents = Text(f_contents)
        ReprHighlighter().highlight(text_contents)
        return text_contents

    @staticmethod
    async def _get_source_path(path_arg: Path) -> CommandResult:
        result = await Commands.exec_chezmoi_cmd(ReadCmd.source_path, path_arg)
        return result

    @staticmethod
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
            result = await Commands.exec_chezmoi_cmd(ReadCmd.git_log, None)
        else:
            source_path_result = await Commands._get_source_path(path_arg)
            if source_path_result.returncode != 0:
                return source_path_result
            result = await Commands.exec_chezmoi_cmd(
                ReadCmd.git_log,
                Path(source_path_result.std_out),
            )
        return result

    @staticmethod
    async def run_chezmoi_diff(diff_cmd: ReadCmd, path: Path) -> CommandResult:
        return await Commands.exec_chezmoi_cmd(diff_cmd, path)


class CheckPath:
    @staticmethod
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

    # functions for both file and dir paths

    @staticmethod
    def _looks_like_cache(path: Path) -> bool:
        path_parts_lower = [p.lower() for p in path.parts]
        return any(
            p.startswith("cache") or p.endswith("cache") for p in path_parts_lower
        )

    # functions for file paths

    @staticmethod
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
    def is_unwanted_dir(dir_path: Path) -> bool:
        return (
            CheckPath._looks_like_cache(dir_path)
            or CheckPath._is_unwanted_dir_name(dir_path)
            or CheckPath._is_git_objects_dir(dir_path)
            or CheckPath._dir_has_many_children(dir_path)
        )
