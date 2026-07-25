from __future__ import annotations

import json
import subprocess
from datetime import datetime
from functools import cache
from itertools import islice
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse.cm_command import UGLY_ARGS, ReadCmd, WriteCmd
from chezmoi_mousse.cm_types import CommandResult
from chezmoi_mousse.str_enums import LogColor, PathFilters

if TYPE_CHECKING:
    from chezmoi_mousse.cm_types import ParsedJson, StrTup

DRY_RUN = "--dry-run"


class RunChezmoi:

    @staticmethod
    def subprocess_args(cmd: ReadCmd | WriteCmd, dry_run: bool) -> StrTup:
        return (
            ("chezmoi",) + cmd.value
            if dry_run is False
            else ("chezmoi", f"{DRY_RUN}") + cmd.value
        )

    @staticmethod
    def full_cmd_str(cmd: ReadCmd | WriteCmd, dry_run: bool) -> str:
        return (
            f"chezmoi {" ".join(cmd.value)}"
            if dry_run is False
            else f"chezmoi {DRY_RUN} {" ".join(cmd.value)}"
        )

    @staticmethod
    def pretty_cmd(
        cmd: ReadCmd | WriteCmd, dry_run: bool, path_arg: Path | None
    ) -> str:
        pretty_cmd = "chezmoi" if dry_run is False else f"chezmoi {DRY_RUN}"
        pretty_cmd += " ".join([a for a in cmd.value if a not in UGLY_ARGS])
        return pretty_cmd if path_arg is None else f"{pretty_cmd} {path_arg}"

    @staticmethod
    def _subprocess_run(
        run_args: StrTup, time_out: int
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            run_args, capture_output=True, shell=False, text=True, timeout=time_out
        )

    @staticmethod
    def _exit_code_colored_cmd(pretty_cmd: str, returncode: int) -> str:
        pretty_time = f"{datetime.now().strftime('%H:%M:%S')}"
        cmd_color = LogColor.success if returncode == 0 else LogColor.warning
        return f"{pretty_time} [${cmd_color}]{pretty_cmd}[/] (returncode {returncode})"

    @staticmethod
    def run(
        cmd: ReadCmd | WriteCmd, *, dry_run: bool, path_arg: Path | None = None
    ) -> CommandResult:
        time_out: int = 10 if isinstance(cmd, ReadCmd) else 20
        run_args = RunChezmoi.subprocess_args(cmd, dry_run) + (str(path_arg),)
        if path_arg is not None:
            run_args += (str(path_arg),)

        completed_process: subprocess.CompletedProcess[str] = (
            RunChezmoi._subprocess_run(run_args, time_out)
        )

        out_lines = [
            line for line in completed_process.stdout.splitlines() if line.strip()
        ]
        std_out = "\n".join(out_lines)

        err_lines = [
            line for line in completed_process.stderr.splitlines() if line.strip()
        ]
        std_err = "\n".join(err_lines)

        if isinstance(cmd, ReadCmd) and cmd in (
            ReadCmd.template_data,
            ReadCmd.dump_config,
        ):
            parsed_json: ParsedJson = json.loads(std_out)
        else:
            parsed_json = {}

        pretty_cmd = RunChezmoi.pretty_cmd(cmd, dry_run, path_arg)
        exit_colored_cmd = RunChezmoi._exit_code_colored_cmd(
            pretty_cmd, completed_process.returncode
        )

        return CommandResult(
            dry_run=dry_run,
            err_lines=err_lines,
            full_cmd_str=RunChezmoi.full_cmd_str(cmd, dry_run),
            out_lines=out_lines,
            parsed_json=parsed_json,
            pretty_cmd=pretty_cmd,
            path_arg=path_arg,
            returncode=completed_process.returncode,
            std_err=std_err,
            std_out=std_out,
            colored_cmd=exit_colored_cmd,
        )


class CheckPath:

    # functions for file paths

    @staticmethod
    @cache
    def is_sensitive(file_path: Path) -> bool:
        return (
            file_path.suffix in PathFilters.KEY_FILE_EXTENSIONS.value
            or file_path.parts[-1] in PathFilters.KEY_FILE_NAMES.value
        )

    @staticmethod
    @cache
    def is_large(file_path: Path) -> bool:
        # check if it's a large file, typically not a dot file
        return file_path.stat().st_size > 1024 * 1024  # 1 MiB

    @staticmethod
    @cache
    def is_binary(file_path: Path) -> bool:
        # check if the file looks like a binary
        try:
            with Path.open(file_path, "rb") as f:
                chunk = f.read(1024)  # Read only first KiB
            return b"\x00" in chunk  # typically the case for binary files
        except OSError:
            return True

    @staticmethod
    @cache
    def is_bad_suffix(file_path: Path) -> bool:
        return file_path.suffix in PathFilters.UNWANTED_FILE_SUFFIXES.value

    # functions for dir paths

    @staticmethod
    @cache
    def is_unwanted_dir_name(dir_path: Path) -> bool:
        return dir_path.parts[-1] in PathFilters.UNWANTED_DIRS.value

    @staticmethod
    @cache
    def is_git_objects_dir(dir_path: Path) -> bool:
        return dir_path.parts[-1] == "objects" and dir_path.parts[-2] == ".git"

    @staticmethod
    @cache
    def is_dest_dir_or_parent(dir_path: Path, dest_dir: Path) -> bool:
        return dir_path == dest_dir or not dir_path.is_relative_to(dest_dir)

    @staticmethod
    @cache
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
    @cache
    def get_unchanged_dir_paths_in(
        dir_path: Path, managed_files: set[Path]
    ) -> list[Path]:
        results: set[Path] = set()
        for path in managed_files:
            if path != dir_path and path.is_relative_to(dir_path):
                results.add(path)
        return sorted(results)

    @staticmethod
    @cache
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
    @cache
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
