from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from itertools import chain
from pathlib import Path

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.cm_types import ManagedResults, ParsedJson, TabIds
from chezmoi_mousse.str_enums import PathKind, StatusCode, TabLabel

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
        # TODO: implement colors for PathKind
        # path_kind_map = {PathKind.path_exists: "text-success"} # noqa: ERA001
        status_code = context[0]
        if status_code is not None and status_code in chezmoi_status_map:
            tag.append(chezmoi_status_map[status_code])
        return f"{tag}]"

    def _is_n_dir(
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

    def _path_kind_dict(
        self, paths: list[Path], unmanaged: bool
    ) -> dict[Path, PathKind]:
        result: dict[Path, PathKind] = {}
        for path in paths:
            if path.is_symlink():
                path_kind = PathKind.symlink
            elif unmanaged is False and path.exists():
                path_kind = PathKind.path_exists
            elif unmanaged is True:
                path_kind = PathKind.unmanaged  # TODO: add PathKind.unwanted
            else:
                path_kind = PathKind.unknown
            result[path] = path_kind
        return result

    def update_fields(self, *, dest_dir: Path, results: ManagedResults) -> None:

        self.clear_cached_properties()

        def _lines_to_paths(lines: list[str]) -> list[Path]:
            return [Path(line) for line in lines]

        def _status_dict(lines: list[str], column: int) -> dict[Path, StatusCode]:
            return {
                Path(line[3:]): StatusCode(line[column])
                for line in lines
                if line[column] != StatusCode.Space
            }

        # no context vars
        _managed_dirs = _lines_to_paths(results.managed_dirs.out_lines)
        _managed_files = _lines_to_paths(results.managed_files.out_lines)
        _unmanaged_dirs = _lines_to_paths(results.unmanaged_dirs.out_lines)
        _unmanaged_files = _lines_to_paths(results.unmanaged_files.out_lines)

        # context vars
        _apply_dirs = _status_dict(results.status_dirs.out_lines, 1)
        _apply_files = _status_dict(results.status_files.out_lines, 1)
        _re_add_dirs = _status_dict(results.status_dirs.out_lines, 0)
        _re_add_files = _status_dict(results.status_files.out_lines, 0)

        # assign results
        self.managed_dirs = self._path_kind_dict(_managed_dirs, unmanaged=False)
        self.managed_files = self._path_kind_dict(_managed_files, unmanaged=False)
        self.apply_dirs = _apply_dirs
        self.apply_files = _apply_files
        self.apply_n_dirs = self._is_n_dir(
            dest_dir=dest_dir,
            tab_label=TabLabel.apply,
            s_dirs=set(_apply_dirs),
            s_files=set(_apply_files),
        )
        self.re_add_dirs = _re_add_dirs
        self.re_add_files = _re_add_files
        self.re_add_n_dirs = self._is_n_dir(
            dest_dir=dest_dir,
            tab_label=TabLabel.re_add,
            s_dirs=set(_re_add_dirs),
            s_files=set(_re_add_files),
        )
        self.unmanaged_dirs = self._path_kind_dict(_unmanaged_dirs, unmanaged=True)
        self.unmanaged_files = self._path_kind_dict(_unmanaged_files, unmanaged=True)


@dataclass(slots=True, kw_only=True)
class CmAttributes:
    ids = TabIds(
        add=AppIds(TabLabel.add),
        apply=AppIds(TabLabel.apply),
        config=AppIds(TabLabel.config),
        debug=AppIds(TabLabel.debug),
        logs=AppIds(TabLabel.logs),
        re_add=AppIds(TabLabel.re_add),
    )

    dry_run: bool = True

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
