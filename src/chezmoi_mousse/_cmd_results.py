from __future__ import annotations

import json
from dataclasses import dataclass, fields
from functools import cache, cached_property
from pathlib import Path
from typing import TYPE_CHECKING, ReadOnly, TypedDict

from ._str_enums import PathKind, StatusCode, TabLabel

if TYPE_CHECKING:
    from typing import Any

    from ._run_cmd import CommandResult

__all__ = ["CachedData"]

type ParsedJson = dict[str, Any]


class PathStatus(TypedDict):
    path: ReadOnly[Path]
    status: ReadOnly[StatusCode]


@dataclass(kw_only=True)
class CmdResults:
    # we cannot use any @cache or @cached_property decorators here as we assign new
    # values to the CommandResult fields after chezmoi operations

    cat_config: CommandResult | None = None
    doctor: CommandResult | None = None
    dump_config: CommandResult | None = None
    git_log: CommandResult | None = None
    ignored: CommandResult | None = None
    managed_dirs: CommandResult | None = None
    managed_files: CommandResult | None = None
    status_dirs: CommandResult | None = None
    status_files: CommandResult | None = None
    template_data: CommandResult | None = None

    @property
    def all(self) -> list[CommandResult | None]:
        return [getattr(self, f.name) for f in fields(self)]

    @property
    def managed_dirs_set(self) -> frozenset[Path]:
        if self.managed_dirs is None or not self.managed_dirs.std_out:
            return frozenset()
        return frozenset(Path(line) for line in self.managed_dirs.std_out.splitlines())

    @property
    def managed_files_set(self) -> frozenset[Path]:
        if self.managed_files is None or not self.managed_files.std_out:
            return frozenset()
        return frozenset(Path(line) for line in self.managed_files.std_out.splitlines())

    @property
    def managed_paths_set(self) -> frozenset[Path]:
        return self.managed_dirs_set | self.managed_files_set

    @property
    def status_dirs_set(self) -> frozenset[Path]:
        if self.status_dirs is None or not self.status_dirs.std_out:
            return frozenset()
        return frozenset(Path(line) for line in self.status_dirs.std_out.splitlines())

    @property
    def status_files_set(self) -> frozenset[Path]:
        if self.status_files is None or not self.status_files.std_out:
            return frozenset()
        return frozenset(Path(line) for line in self.status_files.std_out.splitlines())

    @property
    def status_paths_set(self) -> frozenset[Path]:
        return self.status_dirs_set | self.status_files_set

    @property
    def unchanged_dirs_set(self) -> frozenset[Path]:
        return self.managed_dirs_set - self.status_dirs_set

    @property
    def unchanged_files_set(self) -> frozenset[Path]:
        return self.managed_files_set - self.status_files_set

    @property
    def unchanged_paths_set(self) -> frozenset[Path]:
        return self.unchanged_dirs_set | self.unchanged_files_set

    @property
    def apply_status_dirs(self) -> frozenset[tuple[Path, StatusCode]]:
        if self.status_dirs is None or not self.status_dirs.std_out:
            return frozenset()
        return frozenset(
            (Path(line[3:]), StatusCode(line[0]))
            for line in self.status_dirs.std_out.splitlines()
        )

    @property
    def apply_status_files(self) -> frozenset[tuple[Path, StatusCode]]:
        if self.status_files is None or not self.status_files.std_out:
            return frozenset()
        return frozenset(
            (Path(line[3:]), StatusCode(line[0]))
            for line in self.status_files.std_out.splitlines()
        )

    @property
    def apply_status_paths(self) -> frozenset[tuple[Path, StatusCode]]:
        return self.apply_status_dirs | self.apply_status_files

    @property
    def state_status_dirs(self) -> frozenset[tuple[Path, StatusCode]]:
        if self.status_dirs is None or not self.status_dirs.std_out:
            return frozenset()
        return frozenset(
            (Path(line[3:]), StatusCode(line[1]))
            for line in self.status_dirs.std_out.splitlines()
        )

    @property
    def state_status_files(self) -> frozenset[tuple[Path, StatusCode]]:
        if self.status_files is None or not self.status_files.std_out:
            return frozenset()
        return frozenset(
            (Path(line[3:]), StatusCode(line[1]))
            for line in self.status_files.std_out.splitlines()
        )

    @property
    def state_status_paths(self) -> frozenset[tuple[Path, StatusCode]]:
        return self.state_status_dirs | self.state_status_files

    @property
    def dir_status_lines(self) -> frozenset[str]:
        if self.status_dirs is None or not self.status_dirs.std_out:
            return frozenset()
        return frozenset(self.status_dirs.std_out.splitlines())

    @property
    def file_status_lines(self) -> frozenset[str]:
        if self.status_files is None or not self.status_files.std_out:
            return frozenset()
        return frozenset(self.status_files.std_out.splitlines())

    @property
    def path_status_lines(self) -> frozenset[str]:
        return self.dir_status_lines | self.file_status_lines

    @property
    def parsed_config_dump(self) -> ParsedJson:
        if self.dump_config is None or not self.dump_config.std_out:
            return {}
        return json.loads(self.dump_config.std_out)


type ContextStatus = dict[PathKind, dict[Path, StatusCode]]


@dataclass
class CachedData:
    # this class will be reinitialized after each chezmoi apply, re-add, forget,
    # destroy or add operation

    managed_dirs: frozenset[Path] = frozenset()
    managed_files: frozenset[Path] = frozenset()
    managed_paths: frozenset[Path] = frozenset()

    # paths with any status in the first or second column or both
    status_dirs: frozenset[Path] = frozenset()
    status_files: frozenset[Path] = frozenset()
    status_paths: frozenset[Path] = frozenset()

    # managed paths without any status at all, either in the first or second column
    unchanged_dirs: frozenset[Path] = frozenset()
    unchanged_files: frozenset[Path] = frozenset()
    unchanged_paths: frozenset[Path] = frozenset()

    # lines from the chezmoi status output
    dir_status_lines: frozenset[str] = frozenset()
    file_status_lines: frozenset[str] = frozenset()
    path_status_lines: frozenset[str] = frozenset()

    @cached_property
    def no_managed_paths(self) -> bool:
        return bool(not self.managed_paths)

    # we can safely cache these returns as we create a new new instance of CachedData
    # after each chezmoi operation or manual refresh, cache is cleared post init.

    @classmethod
    @cache
    def _get_status_dict(
        cls, tab_label: TabLabel, path_kind: PathKind, dir_path: Path | None = None
    ) -> dict[Path, StatusCode]:
        if tab_label == TabLabel.apply:
            column = 1
        elif tab_label == TabLabel.re_add:
            column = 0
        else:
            raise NotImplementedError(f"TabLabel not yet implemented: {tab_label}")
        if path_kind == PathKind.dir:
            pairs = {Path(line[3:]): line[:2] for line in cls.dir_status_lines}
        elif path_kind == PathKind.file:
            pairs = {Path(line[3:]): line[:2] for line in cls.file_status_lines}
        elif path_kind == PathKind.both:
            pairs = {Path(line[3:]): line[:2] for line in cls.path_status_lines}
        else:
            raise ValueError(f"Invalid PathKind value: {path_kind}")
        all_status_paths = {
            path: StatusCode(status[column])
            for path, status in pairs.items()
            if status[column] != StatusCode.Space
        }
        if dir_path is None:
            return all_status_paths
        else:
            return {
                path: StatusCode(status[column])
                for path, status in all_status_paths.items()
                if path.is_relative_to(dir_path)
            }

    @classmethod
    @cache
    def get_path_status(cls, tab_label: TabLabel, path: Path) -> dict[Path, StatusCode]:
        if path in cls.status_dirs:
            path_kind = PathKind.dir
        elif path in cls.status_files:
            path_kind = PathKind.file
        else:
            path_kind = PathKind.both
        return cls._get_status_dict(tab_label, path_kind)

    @classmethod
    @cache
    def get_path_status_dict(cls, tab_label: TabLabel) -> dict[Path, StatusCode]:
        return cls._get_status_dict(tab_label, PathKind.dir)

    @classmethod
    @cache
    def tab_status_dirs(cls, tab_label: TabLabel) -> dict[Path, StatusCode]:
        return cls._get_status_dict(tab_label, PathKind.dir)

    @classmethod
    @cache
    def tab_status_files(cls, tab_label: TabLabel) -> dict[Path, StatusCode]:
        return cls._get_status_dict(tab_label, PathKind.file)

    @classmethod
    @cache
    def tab_status_paths(cls, tab_label: TabLabel) -> dict[Path, StatusCode]:
        return cls._get_status_dict(tab_label, PathKind.both)

    @classmethod
    @cache
    def status_files_in(cls, tab_label: TabLabel) -> dict[Path, StatusCode]:
        return cls._get_status_dict(tab_label, PathKind.file)

    @classmethod
    @cache
    def status_dirs_in(cls, dir_path: Path) -> set[Path]:
        return {p for p in cls.status_dirs if p.parent == dir_path}

    @classmethod
    @cache
    def has_status_descendants(cls, tab_label: TabLabel, dir_path: Path) -> bool:
        if dir_path not in cls.managed_dirs:
            raise ValueError(f"An unmanaged dir was received: {dir_path}")
        return any(p.is_relative_to(dir_path) for p in cls.tab_status_paths(tab_label))

    @classmethod
    @cache
    def _get_unchanged_in_by_context(cls, dir_path: Path) -> set[Path]:
        return {p for p in cls.unchanged_dirs if p.parent == dir_path}

    @classmethod
    @cache
    def unchanged_dirs_in(cls, dir_path: Path) -> set[Path]:
        return {p for p in cls.unchanged_dirs if p.parent == dir_path}

    @classmethod
    @cache
    def has_unchanged_paths(cls, dir_path: Path) -> bool:
        return any(p for p in cls.unchanged_paths if p.is_relative_to(dir_path))
