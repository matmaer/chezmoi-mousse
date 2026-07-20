from __future__ import annotations

from dataclasses import dataclass, field
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.chezmoi_command import ChezmoiCommand, CmdResults
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
    dirs: dict[Path, StatusCode] = field(default_factory=lambda: {})
    files: dict[Path, StatusCode] = field(default_factory=lambda: {})
    unmanaged_dirs: dict[Path, StatusCode] = field(default_factory=lambda: {})
    unmanaged_files: dict[Path, StatusCode] = field(default_factory=lambda: {})
    apply_files: dict[Path, StatusCode] = field(default_factory=lambda: {})
    apply_dirs: dict[Path, StatusCode] = field(default_factory=lambda: {})
    re_add_files: dict[Path, StatusCode] = field(default_factory=lambda: {})
    re_add_dirs: dict[Path, StatusCode] = field(default_factory=lambda: {})


@dataclass(frozen=True, kw_only=True)
class ParsedConfig:
    # set by splash screen or refresh or loading modal, will raise attribute error if
    # field is not set or key error if trying to access a property too soon
    cfg: ParsedJson = field(default_factory=lambda: {})

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

    # inits without needing updates later on
    command: ChezmoiCommand = ChezmoiCommand()
    ids: TabIds = TabIds()

    # updated in splash screen
    template_data: ParsedJson = field(default_factory=lambda: {})
    cfg: ParsedConfig = field(default_factory=lambda: ParsedConfig())

    # updated after operations
    changes: ChangedPaths = ChangedPaths()
    managed: ManagedPaths = ManagedPaths()

    @classmethod
    def update_managed_attr(cls) -> None:
        cls.managed = ManagedPaths(
            dirs=CmdResults.get_managed_dict(PathKind.dir),
            files=CmdResults.get_managed_dict(PathKind.file),
            unmanaged_dirs={},
            unmanaged_files={},
            apply_files={},
            apply_dirs={},
            re_add_files={},
            re_add_dirs={},
        )

    @classmethod
    def _get_dirs_with_nested_status(
        cls,
        dest_dir: Path,
        dirs_dict: dict[Path, StatusCode],
        files_dict: dict[Path, StatusCode],
    ) -> dict[Path, StatusCode]:

        # to exclude dirs with a real status
        s_dirs: set[Path] = {p for p, s in dirs_dict.items() if s != StatusCode.Space}

        # consider all files with a real status their parents
        s_files: set[Path] = {p for p, s in files_dict.items() if s != StatusCode.Space}

        # all dirs with status descendants
        s_parents = set(chain.from_iterable(p.parents for p in chain(s_dirs, s_files)))

        # Create a shallow copy so we don't mutate the input dictionary
        dirs_dict_copy = dirs_dict.copy()

        for p in s_parents - s_dirs:
            if not p.is_relative_to(dest_dir) or p == dest_dir:
                continue

            if p not in dirs_dict_copy:
                raise ValueError("Trying to return a new dict with new paths.")

            dirs_dict_copy[p] = StatusCode.N_Dir
        return dirs_dict_copy
