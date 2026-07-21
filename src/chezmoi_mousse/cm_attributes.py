from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.chezmoi_command import (
    ChezmoiCommand,
    CmdResults,
    CommandResult,
    ReadCmd,
    WriteCmd,
)
from chezmoi_mousse.str_enums import PathKind, StatusCode, TabLabel

if TYPE_CHECKING:
    from chezmoi_mousse.type_checking import ParsedJson

__all__ = ["CmAttributes"]


@dataclass(frozen=True, slots=True, kw_only=True)
class ChangedPaths:
    added_paths: list[Path] = field(default_factory=lambda: [])
    changed_status_paths: list[Path] = field(default_factory=lambda: [])
    removed_paths: list[Path] = field(default_factory=lambda: [])

    @property
    def no_changes(self) -> bool:
        return (
            not self.added_paths
            and not self.changed_status_paths
            and not self.removed_paths
        )

    @classmethod
    def clear_changes(cls) -> None:
        cls.changes = ChangedPaths()


@dataclass(slots=True, frozen=True, kw_only=True)
class TabIds:
    add = AppIds(TabLabel.add)
    apply = AppIds(TabLabel.apply)
    config = AppIds(TabLabel.config)
    debug = AppIds(TabLabel.debug)
    logs = AppIds(TabLabel.logs)
    re_add = AppIds(TabLabel.re_add)


@dataclass(slots=True, frozen=True, kw_only=True)
class ManagedPaths:
    dest_dir: Path
    classic_theme_vars: dict[str, str]
    dirs: dict[Path, PathKind] = field(default_factory=lambda: {})
    files: dict[Path, PathKind] = field(default_factory=lambda: {})
    apply_dirs: dict[Path, StatusCode] = field(default_factory=lambda: {})
    apply_files: dict[Path, StatusCode] = field(default_factory=lambda: {})
    re_add_dirs: dict[Path, StatusCode] = field(default_factory=lambda: {})
    re_add_files: dict[Path, StatusCode] = field(default_factory=lambda: {})
    dirs_not_managed: dict[Path, PathKind] = field(default_factory=lambda: {})
    files_not_managed: dict[Path, PathKind] = field(default_factory=lambda: {})

    def _get_n_dirs(self, tab_label: TabLabel) -> set[Path]:
        n_dirs: set[Path] = set()

        # s_dirs var to exclude dirs with a real status and their parents
        # s_files to consider all files with a real status their parents
        if tab_label == TabLabel.apply:
            s_dirs: set[Path] = set(self.apply_dirs)
            s_files: set[Path] = set(self.apply_files)
        elif tab_label == TabLabel.re_add:
            s_dirs: set[Path] = set(self.re_add_dirs)
            s_files: set[Path] = set(self.re_add_files)

        else:
            raise ValueError(f"Trying to get n_dirs for tab {tab_label}")

        # all dirs with status descendants
        s_parents = set(chain.from_iterable(p.parents for p in chain(s_dirs, s_files)))

        for p in s_parents - s_dirs:
            if not p.is_relative_to(self.dest_dir) or p == self.dest_dir:
                continue
            else:
                n_dirs.add(p)
        return n_dirs

    @cached_property
    def apply_n_dirs(self) -> set[Path]:
        return self._get_n_dirs(TabLabel.apply)

    @cached_property
    def re_add_n_dirs(self) -> set[Path]:
        return self._get_n_dirs(TabLabel.re_add)

    @cached_property
    def no_apply_paths(self) -> bool:
        return not self.apply_dirs and not self.apply_files

    @cached_property
    def no_re_add_paths(self) -> bool:
        return not self.re_add_dirs and not self.re_add_files

    @cached_property
    def no_status_paths(self) -> bool:
        return self.no_apply_paths and self.no_re_add_paths

    def _get_tag(
        self, context: tuple[StatusCode | None, PathKind | None] = (None, None)
    ) -> str:
        tag: list[str] = ["["]
        chezmoi_status_map = {
            StatusCode.Added: "text-success",
            StatusCode.Deleted: "text-error",
            StatusCode.Modified: "text-warning",
            StatusCode.Run: "error",  # choose error as it's not yet implemented
        }
        status_code = context[0]
        path_kind = context[1]
        if status_code is None and path_kind is None:
            raise ValueError("Cannot compute tag.")
        elif status_code is not None and status_code in chezmoi_status_map:
            tag.append(chezmoi_status_map[status_code])
        elif path_kind in (PathKind.file_not_managed, PathKind.dir_not_managed):
            tag.append("accent-")
        return f"{tag}]"


@dataclass(frozen=True, kw_only=True)
class ParsedConfig:

    cfg: ParsedJson

    @property
    def dest_dir(self) -> Path:
        return Path(self.cfg["destDir"])

    @property
    def auto_add(self) -> bool:
        return self.cfg["git"]["autoadd"]

    @property
    def auto_commit(self) -> bool:
        return self.cfg["git"]["autocommit"]

    @property
    def auto_push(self) -> bool:
        return self.cfg["git"]["autopush"]


@dataclass
class CmAttributes:

    # initialize in main.py before calling .run() on the app instance
    classic_theme_vars: dict[str, str]
    command: ChezmoiCommand
    ids: TabIds

    # initialize in splash_screen.py before we push the MainScreen
    cfg: ParsedConfig
    managed: ManagedPaths
    template_data: ParsedJson

    # initialize empty
    changes: ChangedPaths = ChangedPaths()

    @staticmethod
    def _status_dict(lines: list[str], column: int) -> dict[Path, StatusCode]:
        return {
            Path(line[3:]): StatusCode(line[column])
            for line in lines
            if line[column] != StatusCode.Space
        }

    @staticmethod
    def _path_kind_dict(command_result: CommandResult) -> dict[Path, PathKind]:
        result: dict[Path, PathKind] = {}
        paths: list[Path] = [Path(line) for line in command_result.out_lines]
        symlink_error = (
            "found a symlink after calling chezmoi with global flag '--mode=file'"
        )
        for path in paths:
            # unmanaged paths
            if command_result.verb_cmd == ReadCmd.unmanaged_dirs:
                result[path] = PathKind.dir_not_managed
            elif command_result.verb_cmd == ReadCmd.unmanaged_files:
                result[path] = PathKind.file_not_managed
            # managed dirs
            elif command_result.verb_cmd == ReadCmd.managed_dirs:
                result[path] = (
                    PathKind.dir_exists if path.is_dir() else PathKind.dir_not_exists
                )
            # managed files
            elif command_result.verb_cmd == ReadCmd.managed_files:
                result[path] = (
                    PathKind.file_exists if path.is_file() else PathKind.file_not_exists
                )
            # raise if symlink is found
            elif path.is_symlink():
                raise ValueError(symlink_error)
            else:
                raise NotImplementedError(f"Path kind not implemented for {path}")
        return result

    @classmethod
    def update_managed_attr(cls, cmd_results: CmdResults) -> None:
        cls.managed = ManagedPaths(
            dest_dir=cls.cfg.dest_dir,
            classic_theme_vars={},
            dirs=cls._path_kind_dict(cmd_results.managed_dirs),
            files=cls._path_kind_dict(cmd_results.managed_files),
            apply_dirs=cls._status_dict(cmd_results.status_dirs.out_lines, 1),
            apply_files=cls._status_dict(cmd_results.status_files.out_lines, 1),
            re_add_dirs=cls._status_dict(cmd_results.status_dirs.out_lines, 0),
            re_add_files=cls._status_dict(cmd_results.status_files.out_lines, 0),
            dirs_not_managed=cls._path_kind_dict(cmd_results.unmanaged_dirs),
            files_not_managed=cls._path_kind_dict(cmd_results.unmanaged_dirs),
        )

    @staticmethod
    def get_command_result(command: ReadCmd | WriteCmd) -> CommandResult:
        # will raise AttributeError if we get it before set
        return getattr(CmdResults, command.name)
