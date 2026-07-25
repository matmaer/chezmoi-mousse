import json
import subprocess
from functools import cache
from itertools import islice
from pathlib import Path

from chezmoi_mousse.cm_command import CommandResult, GlobalArgs, ReadCmd, WriteCmd
from chezmoi_mousse.cm_types import ParsedJson, StrTup
from chezmoi_mousse.str_enums import PathFilters


class RunChezmoi:

    @staticmethod
    def review_cmd(
        cmd: ReadCmd | WriteCmd, *, dry_run: bool | None = None, rel_path: str = ""
    ) -> str:
        if isinstance(cmd, ReadCmd):
            return cmd.pretty_cmd + rel_path
        elif dry_run is not None:
            return cmd.pretty_cmd(write_cmd=cmd, dry_run=dry_run) + rel_path
        else:
            raise ValueError(f"Receiving write cmd {cmd} and dry run is {dry_run}")

    @staticmethod
    def _subprocess_run(
        run_args: StrTup, time_out: int
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            run_args, capture_output=True, shell=False, text=True, timeout=time_out
        )

    @staticmethod
    def run(
        cmd: ReadCmd | WriteCmd,
        *,
        dry_run: bool | None = None,
        path_arg: Path | None = None,
    ) -> CommandResult:
        time_out: int = 10 if isinstance(cmd, ReadCmd) else 20
        if isinstance(cmd, WriteCmd):
            if dry_run is None:
                raise ValueError(f"dry_run is None for a write cmd: {cmd}")
            else:
                full_cmd_str = cmd.full_cmd_str(cmd, dry_run)
                run_args = cmd.subprocess_args(cmd, dry_run) + (str(path_arg),)
        else:
            full_cmd_str = cmd.full_cmd_str
            run_args = cmd.subprocess_args + (str(path_arg),)

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

        return CommandResult(
            dry_run=GlobalArgs.dry_run in run_args,
            err_lines=err_lines,
            full_cmd=full_cmd_str,
            out_lines=out_lines,
            parsed_json=parsed_json,
            path_arg=path_arg,
            returncode=completed_process.returncode,
            std_err=std_err,
            std_out=std_out,
            verb_cmd=cmd,
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
