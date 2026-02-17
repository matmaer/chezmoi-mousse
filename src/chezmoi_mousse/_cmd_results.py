from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from ._singletons import CommandResults
from ._str_enums import StatusCode
from ._type_hinting import DirNode

if TYPE_CHECKING:
    from typing import Any

    from ._chezmoi_command import CommandResult

__all__ = ["CmdResults"]


class ReactiveDataclass:
    # Base class for dataclasses to trigger logic on field updates.
    # The calls to super().__setattr__() ensure that Python internals work correctly.

    def __setattr__(self, name: str, value: Any) -> None:
        if hasattr(self, name):
            old_value = getattr(self, name)
            super().__setattr__(name, value)
            if old_value != value:
                self._on_field_change(name)
        else:
            super().__setattr__(name, value)

    def _on_field_change(self, name: str) -> None:
        # Override in subclasses to define update logic
        pass


@dataclass(slots=True)
class ChangedPaths:
    added_managed_dirs: list[Path] = field(default_factory=list[Path])
    removed_managed_dirs: list[Path] = field(default_factory=list[Path])
    added_managed_files: list[Path] = field(default_factory=list[Path])
    removed_managed_files: list[Path] = field(default_factory=list[Path])
    added_status_dirs: list[Path] = field(default_factory=list[Path])
    removed_status_dirs: list[Path] = field(default_factory=list[Path])
    added_status_files: list[Path] = field(default_factory=list[Path])
    removed_status_files: list[Path] = field(default_factory=list[Path])
    changed_apply_status_dirs: dict[Path, StatusCode] = field(
        default_factory=dict[Path, StatusCode]
    )
    changed_re_add_status_dirs: dict[Path, StatusCode] = field(
        default_factory=dict[Path, StatusCode]
    )
    changed_apply_status_files: dict[Path, StatusCode] = field(
        default_factory=dict[Path, StatusCode]
    )
    changed_re_add_status_files: dict[Path, StatusCode] = field(
        default_factory=dict[Path, StatusCode]
    )


@dataclass(slots=True)
class CmdResults(ReactiveDataclass):
    new_results: CommandResults = field(default_factory=CommandResults)
    changed_paths: ChangedPaths = field(default_factory=ChangedPaths)
    dest_dir: Path = Path.home()
    git_auto_add: bool = False
    git_auto_commit: bool = False
    git_auto_push: bool = False
    managed_dirs: list[Path] = field(default_factory=list[Path])
    managed_files: list[Path] = field(default_factory=list[Path])
    apply_status_dirs: dict[Path, StatusCode] = field(
        default_factory=dict[Path, StatusCode]
    )
    apply_status_files: dict[Path, StatusCode] = field(
        default_factory=dict[Path, StatusCode]
    )
    re_add_status_dirs: dict[Path, StatusCode] = field(
        default_factory=dict[Path, StatusCode]
    )
    re_add_status_files: dict[Path, StatusCode] = field(
        default_factory=dict[Path, StatusCode]
    )
    x_dirs: list[Path] = field(default_factory=list[Path])
    x_files: list[Path] = field(default_factory=list[Path])
    apply_dir_nodes: dict[Path, DirNode] = field(default_factory=dict[Path, DirNode])
    re_add_dir_nodes: dict[Path, DirNode] = field(default_factory=dict[Path, DirNode])

    def _on_field_change(self, name: str) -> None:
        if name != "new_results":
            return
        if self.new_results.dump_config is not None:
            parsed_config = json.loads(
                self.new_results.dump_config.completed_process.stdout
            )
            self.git_auto_add = parsed_config["git"]["autoadd"]
            self.git_auto_commit = parsed_config["git"]["autocommit"]
            self.git_auto_push = parsed_config["git"]["autopush"]
            self.dest_dir = Path(parsed_config["destDir"])

        if self.new_results.managed_dirs is not None:
            old_dirs = self.managed_dirs
            new_dirs = [self.dest_dir] + [
                Path(line)
                for line in self.new_results.managed_dirs.std_out.splitlines()
            ]
            self.changed_paths.added_managed_dirs = [
                d for d in new_dirs if d not in old_dirs
            ]
            self.changed_paths.removed_managed_dirs = [
                d for d in old_dirs if d not in new_dirs
            ]
            self.managed_dirs = new_dirs

        if self.new_results.managed_files is not None:
            old_files = self.managed_files
            new_files = [
                Path(line)
                for line in self.new_results.managed_files.std_out.splitlines()
            ]
            self.changed_paths.added_managed_files = [
                f for f in new_files if f not in old_files
            ]
            self.changed_paths.removed_managed_files = [
                f for f in old_files if f not in new_files
            ]
            self.managed_files = new_files

        if self.new_results.status_dirs is not None:
            old_apply = self.apply_status_dirs
            old_re_add = self.re_add_status_dirs
            new_apply = self._parse_status_output(self.new_results.status_dirs, index=0)
            new_re_add = self._parse_status_output(
                self.new_results.status_dirs, index=1
            )
            changed_apply = {
                k: v
                for k, v in new_apply.items()
                if k not in old_apply or old_apply.get(k) != v
            }
            changed_re_add = {
                k: v
                for k, v in new_re_add.items()
                if k not in old_re_add or old_re_add.get(k) != v
            }
            self.changed_paths.changed_apply_status_dirs = changed_apply
            self.changed_paths.changed_re_add_status_dirs = changed_re_add
            self.apply_status_dirs = new_apply
            self.re_add_status_dirs = new_re_add

        if self.new_results.status_files is not None:
            old_apply = self.apply_status_files
            old_re_add = self.re_add_status_files
            new_apply = self._parse_status_output(
                self.new_results.status_files, index=0
            )
            new_re_add = self._parse_status_output(
                self.new_results.status_files, index=1
            )
            changed_apply = {
                k: v
                for k, v in new_apply.items()
                if k not in old_apply or old_apply.get(k) != v
            }
            changed_re_add = {
                k: v
                for k, v in new_re_add.items()
                if k not in old_re_add or old_re_add.get(k) != v
            }
            self.changed_paths.changed_apply_status_files = changed_apply
            self.changed_paths.changed_re_add_status_files = changed_re_add
            self.apply_status_files = new_apply
            self.re_add_status_files = new_re_add

            self._update_x_files()
            self._update_apply_dir_nodes()
            self._update_re_add_dir_nodes()

    def _update_x_dirs(self) -> None:
        self.x_dirs = [
            path for path in self.managed_dirs if path not in self.apply_status_dirs
        ]

    def _update_x_files(self) -> None:
        self.x_files = [
            path for path in self.managed_files if path not in self.apply_status_files
        ]

    def _status_dirs_in(self, dir_path: Path) -> dict[Path, StatusCode]:
        if not self.apply_status_files and not self.apply_status_dirs:
            return {}
        return {
            path: status
            for path, status in self.apply_status_dirs.items()
            if path.is_relative_to(dir_path)
        }

    def _status_files_in(self, dir_path: Path) -> dict[Path, StatusCode]:
        if not self.apply_status_files and not self.apply_status_dirs:
            return {}
        return {
            path: status
            for path, status in self.apply_status_files.items()
            if path.is_relative_to(dir_path)
        }

    def _x_dirs_in(self, dir_path: Path) -> list[Path]:
        if not self.x_files and not self.x_dirs:
            return []
        return [path for path in self.x_dirs if path.is_relative_to(dir_path)]

    def _x_files_in(self, dir_path: Path) -> list[Path]:
        if not self.x_files and not self.x_dirs:
            return []
        return [path for path in self.x_files if path.is_relative_to(dir_path)]

    def _update_apply_dir_nodes(self) -> None:
        result: dict[Path, DirNode] = {}
        for dir_path in self.managed_dirs:
            dir_status = self.apply_status_dirs.get(dir_path, StatusCode.No_Status)
            status_file_children = {
                path: status
                for path, status in self.apply_status_files.items()
                if path.parent == dir_path
            }
            x_files_children = {
                path: StatusCode.No_Status
                for path in self.managed_files
                if path.parent == dir_path and path not in self.apply_status_files
            }
            result[dir_path] = DirNode(
                dir_status=dir_status,
                status_files=status_file_children,
                x_files=x_files_children,
                status_dirs_in=self._status_dirs_in(dir_path),
                status_files_in=self._status_files_in(dir_path),
                x_dirs_in=self._x_dirs_in(dir_path),
                x_files_in=self._x_files_in(dir_path),
            )
        self.apply_dir_nodes = result

    def _update_re_add_dir_nodes(self) -> None:
        result: dict[Path, DirNode] = {}
        for dir_path in self.managed_dirs:
            status_file_children = {
                path: status
                for path, status in self.re_add_status_files.items()
                if path.parent == dir_path
            }
            x_files_children = {
                path: status
                for path, status in self.re_add_status_files.items()
                if path.parent == dir_path
            }
            dir_status = self.re_add_status_dirs.get(dir_path, StatusCode.No_Status)
            result[dir_path] = DirNode(
                dir_status=dir_status,
                status_files=status_file_children,
                x_files=x_files_children,
                status_dirs_in=self._status_dirs_in(dir_path),
                status_files_in=self._status_files_in(dir_path),
                x_dirs_in=self._x_dirs_in(dir_path),
                x_files_in=self._x_files_in(dir_path),
            )
        self.re_add_dir_nodes = result

    def _parse_status_output(
        self, status_results: "CommandResult", index: int
    ) -> dict[Path, StatusCode]:
        status_dict: dict[Path, StatusCode] = {}
        for line in status_results.std_out.splitlines():
            parsed_path = Path(line[3:])
            status_dict[parsed_path] = StatusCode(line[index])
        return status_dict
