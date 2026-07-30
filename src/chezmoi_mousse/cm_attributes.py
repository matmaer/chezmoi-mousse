from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.cm_command import ReadCmd
from chezmoi_mousse.cm_types import (
    ManagedResults,
    PathKindDict,
    ReadCmdGroups,
    SplashResults,
)
from chezmoi_mousse.str_enums import PathKind, StatusCode, TabLabel

if TYPE_CHECKING:
    from chezmoi_mousse.cm_types import ParsedJson, PathKindDict, StatusDict

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


@dataclass(frozen=True, kw_only=True)
class ManagedPaths:
    managed_dirs: PathKindDict = field(default_factory=lambda: {})
    managed_files: PathKindDict = field(default_factory=lambda: {})

    apply_dirs: StatusDict = field(default_factory=lambda: {})
    apply_files: StatusDict = field(default_factory=lambda: {})
    re_add_dirs: StatusDict = field(default_factory=lambda: {})
    re_add_files: StatusDict = field(default_factory=lambda: {})

    apply_n_dirs: PathKindDict = field(default_factory=lambda: {})
    re_add_n_dirs: PathKindDict = field(default_factory=lambda: {})

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

    @cached_property
    def managed_paths(self) -> PathKindDict:
        return self.managed_dirs | self.managed_files


@dataclass
class CmAttributes:

    dest_dir: Path = field(init=False)
    auto_add: bool = field(init=False)
    auto_commit: bool = field(init=False)
    auto_push: bool = field(init=False)
    splash_results: SplashResults = field(init=False)
    parsed_template_data: ParsedJson = field(init=False)
    parsed_dump_config: ParsedJson = field(init=False)

    add_id = AppIds(TabLabel.add)
    apply_id = AppIds(TabLabel.apply)
    config_id = AppIds(TabLabel.config)
    debug_id = AppIds(TabLabel.debug)
    logs_id = AppIds(TabLabel.logs)
    re_add_id = AppIds(TabLabel.re_add)

    read_cmd_groups: ReadCmdGroups = field(
        default=ReadCmdGroups(
            splash_only=[
                ReadCmd.doctor,
                ReadCmd.git_log,
                ReadCmd.cat_config,
                ReadCmd.ignored,
                ReadCmd.git_remote,
            ],
            json_output=[ReadCmd.dump_config, ReadCmd.template_data],
            managed=[
                ReadCmd.managed_dirs,
                ReadCmd.managed_files,
                ReadCmd.status_dirs,
                ReadCmd.status_files,
            ],
        ),
        repr=False,
    )

    dry_run: bool = field(default=True)
    changes: ChangedPaths = ChangedPaths()
    paths: ManagedPaths = ManagedPaths()

    def update_paths(self, results: ManagedResults) -> None:

        def _status_dicts(lines: list[str]) -> tuple[StatusDict, StatusDict]:
            apply: StatusDict = {}
            re_add: StatusDict = {}
            for line in lines:
                path = Path(line[3:])
                apply_status = StatusCode(line[1])
                if apply_status != StatusCode.Space:
                    apply[path] = apply_status
                re_add_status = StatusCode(line[0])
                if re_add_status != StatusCode.Space:
                    re_add[path] = re_add_status
            return apply, re_add

        def _is_n_dir(
            path_kind: PathKind, *, s_dirs: set[Path], s_files: set[Path]
        ) -> PathKindDict:
            n_dirs: PathKindDict = {}

            # s_dirs var to exclude dirs with a real status and their parents
            # s_files to consider all files with a real status their parents

            # all dirs with status descendants
            s_parents = set(
                chain.from_iterable(p.parents for p in chain(s_dirs, s_files))
            )
            for p in s_parents - s_dirs:
                if not p.is_relative_to(results.dest_dir) or p == results.dest_dir:
                    continue
                else:
                    n_dirs[p] = path_kind
            return dict(sorted(n_dirs.items()))

        def _managed_path_kind_dict(lines: list[str]) -> PathKindDict:
            result: PathKindDict = {}
            for line in lines:
                path = Path(line)
                if path.is_dir():
                    result[path] = PathKind.man_dir_exists
                elif path.is_file():
                    result[path] = PathKind.man_file_exists
            return result

        # context vars
        _apply_dirs, _re_add_dirs = _status_dicts(results.status_dirs.out_lines)
        _apply_files, _re_add_files = _status_dicts(results.status_files.out_lines)

        # set new instance on the paths class var
        self.paths = ManagedPaths(
            managed_dirs=_managed_path_kind_dict(results.managed_dirs.out_lines),
            managed_files=_managed_path_kind_dict(results.managed_files.out_lines),
            apply_dirs=_apply_dirs,
            apply_files=_apply_files,
            apply_n_dirs=_is_n_dir(
                PathKind.apply_n_dir, s_dirs=set(_apply_dirs), s_files=set(_apply_files)
            ),
            re_add_dirs=_re_add_dirs,
            re_add_files=_re_add_files,
            re_add_n_dirs=_is_n_dir(
                PathKind.re_add_n_dir,
                s_dirs=set(_re_add_dirs),
                s_files=set(_re_add_files),
            ),
        )
