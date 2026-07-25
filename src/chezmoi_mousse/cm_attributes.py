from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse.app_ids import TabIds
from chezmoi_mousse.cm_command import CommandResult, ReadCmd
from chezmoi_mousse.str_enums import PathKind, StatusCode, TabLabel

if TYPE_CHECKING:
    from chezmoi_mousse.cm_types import ParsedJson

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
        cls.added_paths: list[Path] = []
        cls.changed_status_paths: list[Path] = []
        cls.removed_paths: list[Path] = []


@dataclass(slots=True, kw_only=True)
class ManagedPaths:
    managed_dirs: dict[Path, PathKind] = field(default_factory=lambda: {})
    managed_files: dict[Path, PathKind] = field(default_factory=lambda: {})

    apply_dirs: dict[Path, StatusCode] = field(default_factory=lambda: {})
    apply_files: dict[Path, StatusCode] = field(default_factory=lambda: {})
    re_add_dirs: dict[Path, StatusCode] = field(default_factory=lambda: {})
    re_add_files: dict[Path, StatusCode] = field(default_factory=lambda: {})

    apply_n_dirs: dict[Path, PathKind] = field(default_factory=lambda: {})
    re_add_n_dirs: dict[Path, PathKind] = field(default_factory=lambda: {})

    unmanaged_dirs: dict[Path, PathKind] = field(default_factory=lambda: {})
    unmanaged_files: dict[Path, PathKind] = field(default_factory=lambda: {})

    @cached_property
    def no_apply_paths(self) -> bool:
        return not self.apply_dirs and not self.apply_files

    @cached_property
    def no_re_add_paths(self) -> bool:
        return not self.re_add_dirs and not self.re_add_files

    @cached_property
    def no_status_paths(self) -> bool:
        return self.no_apply_paths and self.no_re_add_paths

    @cached_property
    def no_managed_paths(self) -> bool:
        return not self.managed_dirs and not self.managed_files

    def clear_cached_properties(self) -> None:
        # get all properties which have a .clear_cache() method and call it
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, "clear_cache"):
                attr.clear_cache()

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

    def _compute_n_dirs(
        self,
        *,
        dest_dir: Path,
        tab_label: TabLabel,
        s_dirs: set[Path],
        s_files: set[Path],
    ) -> dict[Path, PathKind]:
        n_dirs: dict[Path, PathKind] = {}

        path_kind = (
            PathKind.apply_n_dir
            if tab_label == TabLabel.apply
            else PathKind.re_add_n_dir
        )

        # s_dirs var to exclude dirs with a real status and their parents
        # s_files to consider all files with a real status their parents

        # all dirs with status descendants
        s_parents = set(chain.from_iterable(p.parents for p in chain(s_dirs, s_files)))
        for p in s_parents - s_dirs:
            if not p.is_relative_to(dest_dir) or p == dest_dir:
                continue
            else:
                n_dirs[p] = path_kind
        return dict(sorted(n_dirs.items()))

    def _path_kind_dict(self, command_result: CommandResult) -> dict[Path, PathKind]:
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

    def _status_dict(self, lines: list[str], column: int) -> dict[Path, StatusCode]:
        return {
            Path(line[3:]): StatusCode(line[column])
            for line in lines
            if line[column] != StatusCode.Space
        }

    def update_fields(
        self,
        *,
        dest_dir: Path,
        status_dirs: CommandResult,
        status_files: CommandResult,
        managed_files: CommandResult,
        managed_dirs: CommandResult,
        unmanaged_files: CommandResult,
        unmanaged_dirs: CommandResult,
    ) -> None:

        self.clear_cached_properties()

        apply_dirs = self._status_dict(status_dirs.out_lines, 1)
        apply_files = self._status_dict(status_files.out_lines, 1)
        re_add_dirs = self._status_dict(status_dirs.out_lines, 0)
        re_add_files = self._status_dict(status_files.out_lines, 0)

        self.managed_dirs = self._path_kind_dict(managed_dirs)
        self.managed_files = self._path_kind_dict(managed_files)
        self.apply_dirs = apply_dirs
        self.apply_files = apply_files
        self.apply_n_dirs = self._compute_n_dirs(
            dest_dir=dest_dir,
            tab_label=TabLabel.apply,
            s_dirs=set(apply_dirs),
            s_files=set(apply_files),
        )
        self.re_add_dirs = re_add_dirs
        self.re_add_files = re_add_files
        self.re_add_n_dirs = self._compute_n_dirs(
            dest_dir=dest_dir,
            tab_label=TabLabel.re_add,
            s_dirs=set(re_add_dirs),
            s_files=set(re_add_files),
        )
        self.unmanaged_dirs = self._path_kind_dict(unmanaged_dirs)
        self.unmanaged_files = self._path_kind_dict(unmanaged_files)


@dataclass(slots=True, kw_only=True)
class CmAttributes:
    dry_run: bool = True

    ids: TabIds = TabIds()

    changes: ChangedPaths = ChangedPaths()
    paths: ManagedPaths = field(default_factory=lambda: ManagedPaths())

    parsed_config_dump: ParsedJson = field(default_factory=lambda: {})
    parsed_template_data: ParsedJson = field(default_factory=lambda: {})

    @cached_property
    def dest_dir(self) -> Path:
        return Path(self.parsed_config_dump["destDir"])

    @cached_property
    def auto_add(self) -> bool:
        return self.parsed_config_dump["git"]["autoadd"]

    @cached_property
    def auto_commit(self) -> bool:
        return self.parsed_config_dump["git"]["autocommit"]

    @cached_property
    def auto_push(self) -> bool:
        return self.parsed_config_dump["git"]["autopush"]

    @cached_property
    def template_data(self) -> ParsedJson:
        return self.parsed_template_data
