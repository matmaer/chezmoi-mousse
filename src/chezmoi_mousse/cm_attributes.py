from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.cm_command import ReadCmd
from chezmoi_mousse.cm_types import ManagedResults, ReadCmdGroups, SplashResults, TabIds
from chezmoi_mousse.str_enums import PathFilters, PathKind, StatusCode, TabLabel

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

    unmanaged_dirs: PathKindDict = field(default_factory=lambda: {})
    unmanaged_files: PathKindDict = field(default_factory=lambda: {})

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

    def get_tag(
        self, context: tuple[StatusCode | None, PathKind | None] = (None, None)
    ) -> str:
        tag: list[str] = ["["]
        chezmoi_status_map = {
            StatusCode.Added: "text-success",
            StatusCode.Deleted: "text-error",
            StatusCode.Modified: "text-warning",
            StatusCode.Run: "error",  # choose error as it's not yet implemented
        }
        # TODO: implement colors for PathKind
        # path_kind_map = {PathKind.path_exists: "text-success"} # noqa: ERA001
        status_code = context[0]
        if status_code is not None and status_code in chezmoi_status_map:
            tag.append(chezmoi_status_map[status_code])
        return f"{tag}]"


@dataclass
class CmAttributes:

    dest_dir: Path = field(init=False)
    auto_add: bool = field(init=False)
    auto_commit: bool = field(init=False)
    auto_push: bool = field(init=False)
    splash_results: SplashResults = field(init=False)
    parsed_template_data: ParsedJson = field(init=False)
    parsed_dump_config: ParsedJson = field(init=False)

    ids: TabIds = field(
        default=TabIds(
            add=AppIds(TabLabel.add),
            apply=AppIds(TabLabel.apply),
            config=AppIds(TabLabel.config),
            debug=AppIds(TabLabel.debug),
            logs=AppIds(TabLabel.logs),
            re_add=AppIds(TabLabel.re_add),
        ),
        repr=False,
    )

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
                ReadCmd.unmanaged_dirs,
                ReadCmd.unmanaged_files,
            ],
        ),
        repr=False,
    )

    dry_run: bool = field(default=True)
    changes: ChangedPaths = ChangedPaths()
    paths: ManagedPaths = ManagedPaths()

    def update_paths(self, results: ManagedResults) -> None:

        def _status_dict(lines: list[str], column: int) -> StatusDict:
            return {
                Path(line[3:]): StatusCode(line[column])
                for line in lines
                if line[column] != StatusCode.Space
            }

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
            for path in [Path(line) for line in lines]:
                if path.exists():
                    result[path] = PathKind.path_exists
                else:
                    result[path] = PathKind.path_not_exists
            return result

        def _unmanaged_dir_kind_dict(lines: list[str]) -> PathKindDict:
            result: PathKindDict = {}
            for path in [Path(line) for line in lines]:
                if path.parts[-1] in PathFilters.UNWANTED_DIRS.value:
                    result[path] = PathKind.unwanted
                elif path.is_symlink():
                    result[path] = PathKind.symlink
                else:
                    result[path] = PathKind.unknown
            return result

        def _unmanaged_file_kind_dict(lines: list[str]) -> PathKindDict:
            result: PathKindDict = {}
            for path in [Path(line) for line in lines]:
                if (
                    path.suffix in PathFilters.KEY_FILE_EXTENSIONS.value
                    or path.suffix in PathFilters.UNWANTED_FILE_SUFFIXES.value
                    or path.parts[-1] in PathFilters.KEY_FILE_NAMES.value
                ):
                    result[path] = PathKind.unwanted
                elif path.is_symlink():
                    result[path] = PathKind.symlink
                else:
                    result[path] = PathKind.unknown
            return result

        # context vars
        _apply_dirs = _status_dict(results.status_dirs.out_lines, 1)
        _apply_files = _status_dict(results.status_files.out_lines, 1)
        _re_add_dirs = _status_dict(results.status_dirs.out_lines, 0)
        _re_add_files = _status_dict(results.status_files.out_lines, 0)

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
            unmanaged_dirs=_unmanaged_dir_kind_dict(results.unmanaged_dirs.out_lines),
            unmanaged_files=_unmanaged_file_kind_dict(
                results.unmanaged_files.out_lines
            ),
        )
