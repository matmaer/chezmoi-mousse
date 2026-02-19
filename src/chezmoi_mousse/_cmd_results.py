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
    added_managed_files: list[Path] = field(default_factory=list[Path])
    removed_managed_dirs: list[Path] = field(default_factory=list[Path])
    removed_managed_files: list[Path] = field(default_factory=list[Path])
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
    removed_status_dirs: list[Path] = field(default_factory=list[Path])
    removed_status_files: list[Path] = field(default_factory=list[Path])


@dataclass(slots=True)
class ParsedConfig:
    dest_dir: Path = Path.home()
    git_auto_add: bool = False
    git_auto_commit: bool = False
    git_auto_push: bool = False


@dataclass(slots=True)
class ParsedPaths:
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


@dataclass(slots=True)
class CmdResults(ReactiveDataclass):
    new_results: CommandResults = field(default_factory=CommandResults)
    changed_paths: ChangedPaths = field(default_factory=ChangedPaths)
    parsed_config: ParsedConfig = field(default_factory=ParsedConfig)
    parsed_paths: ParsedPaths = field(default_factory=ParsedPaths)
    apply_dir_nodes: dict[Path, DirNode] = field(default_factory=dict[Path, DirNode])
    re_add_dir_nodes: dict[Path, DirNode] = field(default_factory=dict[Path, DirNode])
    _status_paths: set[Path] = field(default_factory=lambda: set())
    _dirs_with_status_children: set[Path] = field(default_factory=lambda: set())

    def _on_field_change(self, name: str) -> None:
        if name != "new_results":
            return
        if self.new_results.dump_config is not None:
            self._update_dump_config(self.new_results.dump_config)

        if (
            self.new_results.managed_dirs is None
            or self.new_results.managed_files is None
            or self.new_results.status_dirs is None
            or self.new_results.status_files is None
        ):
            raise ValueError(
                "One of the required CommandResults is None. Cannot update CmdResults."
            )

        self._update_managed_dirs(self.new_results.managed_dirs)
        self._update_managed_files(self.new_results.managed_files)
        self._update_status_dirs(self.new_results.status_dirs)
        self._update_status_files(self.new_results.status_files)
        # Update caches
        self._status_paths = set(self.parsed_paths.apply_status_dirs.keys()) | set(
            self.parsed_paths.apply_status_files.keys()
        )
        self._dirs_with_status_children = set()
        for path in self._status_paths:
            current = path.parent
            while current != current.parent:
                self._dirs_with_status_children.add(current)
                current = current.parent
        # Now update dir nodes as they depend the above
        self._update_apply_dir_nodes()
        self._update_re_add_dir_nodes()

    def _update_dump_config(self, dump_config_result: CommandResult) -> None:
        parsed_config = json.loads(dump_config_result.completed_process.stdout)
        self.parsed_config = ParsedConfig(
            dest_dir=Path(parsed_config["destDir"]),
            git_auto_add=parsed_config["git"]["autoadd"],
            git_auto_commit=parsed_config["git"]["autocommit"],
            git_auto_push=parsed_config["git"]["autopush"],
        )

    def _update_managed_dirs(self, managed_dirs: CommandResult) -> None:
        old_dirs = self.parsed_paths.managed_dirs
        new_dirs = [self.parsed_config.dest_dir] + [
            Path(line) for line in managed_dirs.std_out.splitlines()
        ]
        self.changed_paths.added_managed_dirs = [
            d for d in new_dirs if d not in old_dirs
        ]
        self.changed_paths.removed_managed_dirs = [
            d for d in old_dirs if d not in new_dirs
        ]
        self.parsed_paths.managed_dirs = new_dirs
        self.changed_paths.removed_status_dirs = self.changed_paths.removed_managed_dirs

    def _update_managed_files(self, managed_files: CommandResult) -> None:
        old_files = self.parsed_paths.managed_files
        new_files = [Path(line) for line in managed_files.std_out.splitlines()]
        self.changed_paths.added_managed_files = [
            f for f in new_files if f not in old_files
        ]
        self.changed_paths.removed_managed_files = [
            f for f in old_files if f not in new_files
        ]
        self.parsed_paths.managed_files = new_files
        self.changed_paths.removed_status_files = (
            self.changed_paths.removed_managed_files
        )

    def _parse_status_output(
        self, status_results: "CommandResult", index: int
    ) -> dict[Path, StatusCode]:
        status_dict: dict[Path, StatusCode] = {}
        for line in status_results.std_out.splitlines():
            parsed_path = Path(line[3:])
            status_dict[parsed_path] = StatusCode(line[index])
        return status_dict

    def _update_status_dirs(self, status_dirs: CommandResult) -> None:
        old_apply = self.parsed_paths.apply_status_dirs
        old_re_add = self.parsed_paths.re_add_status_dirs
        new_apply = self._parse_status_output(status_dirs, index=0)
        new_re_add = self._parse_status_output(status_dirs, index=1)
        self.changed_paths.apply_status_dirs = {
            k: v
            for k, v in new_apply.items()
            if k not in old_apply or old_apply[k] != v
        }
        self.changed_paths.re_add_status_dirs = {
            k: v
            for k, v in new_re_add.items()
            if k not in old_re_add or old_re_add[k] != v
        }
        self.parsed_paths.apply_status_dirs = new_apply
        self.parsed_paths.re_add_status_dirs = new_re_add

    def _update_status_files(self, status_files: CommandResult) -> None:
        old_apply = self.parsed_paths.apply_status_files
        old_re_add = self.parsed_paths.re_add_status_files
        new_apply = self._parse_status_output(status_files, index=0)
        new_re_add = self._parse_status_output(status_files, index=1)
        self.changed_paths.apply_status_files = {
            k: v
            for k, v in new_apply.items()
            if k not in old_apply or old_apply[k] != v
        }
        self.changed_paths.re_add_status_files = {
            k: v
            for k, v in new_re_add.items()
            if k not in old_re_add or old_re_add[k] != v
        }
        self.parsed_paths.apply_status_files = new_apply
        self.parsed_paths.re_add_status_files = new_re_add

    def _get_x_files_in(self, dir_path: Path) -> dict[Path, StatusCode]:
        # x files are the same for apply and re_add contexts
        return {
            path: StatusCode.No_Status
            for path in self.parsed_paths.managed_files
            if path.parent == dir_path and path not in self._status_paths
        }

    def _get_x_dirs_in(self, dir_path: Path) -> dict[Path, StatusCode]:
        # x dirs are the same for apply and re_add contexts
        return {
            path: StatusCode.No_Status
            for path in self.parsed_paths.managed_dirs
            if path.parent == dir_path and path not in self._status_paths
        }

    def _get_dirs_for_tree(
        self, dir_path: Path, status_dirs: dict[Path, StatusCode]
    ) -> dict[Path, StatusCode]:
        sub_dir_paths = [
            p for p in self.parsed_paths.managed_dirs if p.parent == dir_path
        ]
        result: dict[Path, StatusCode] = {}
        for sub_dir in sub_dir_paths:
            if sub_dir in status_dirs:
                result[sub_dir] = status_dirs[sub_dir]
            elif sub_dir in self._dirs_with_status_children:
                result[sub_dir] = StatusCode.No_Status
        return dict(sorted(result.items()))

    def _update_apply_dir_nodes(self) -> None:
        for dir_path in self.parsed_paths.managed_dirs:
            dir_status = self.parsed_paths.apply_status_dirs.get(
                dir_path, StatusCode.No_Status
            )
            status_files_in = {
                path: status
                for path, status in self.parsed_paths.apply_status_files.items()
                if path.parent == dir_path
            }
            status_dirs_in = {
                path: status
                for path, status in self.parsed_paths.apply_status_dirs.items()
                if path.parent == dir_path
            }
            self.apply_dir_nodes[dir_path] = DirNode(
                dir_status=dir_status,
                status_dirs_in=status_dirs_in,
                status_files_in=status_files_in,
                x_dirs_in=self._get_x_dirs_in(dir_path),
                x_files_in=self._get_x_files_in(dir_path),
                dirs_in_for_tree=self._get_dirs_for_tree(
                    dir_path, self.parsed_paths.apply_status_dirs
                ),
            )

    def _update_re_add_dir_nodes(self) -> None:
        for dir_path in self.parsed_paths.managed_dirs:
            dir_status = self.parsed_paths.re_add_status_dirs.get(
                dir_path, StatusCode.No_Status
            )
            status_files_in = {
                path: status
                for path, status in self.parsed_paths.re_add_status_files.items()
                if path.parent == dir_path
            }
            status_dirs_in = {
                path: status
                for path, status in self.parsed_paths.re_add_status_dirs.items()
                if path.parent == dir_path
            }
            self.re_add_dir_nodes[dir_path] = DirNode(
                dir_status=dir_status,
                status_dirs_in=status_dirs_in,
                status_files_in=status_files_in,
                x_dirs_in=self._get_x_dirs_in(dir_path),
                x_files_in=self._get_x_files_in(dir_path),
                dirs_in_for_tree=self._get_dirs_for_tree(
                    dir_path, self.parsed_paths.re_add_status_dirs
                ),
            )
