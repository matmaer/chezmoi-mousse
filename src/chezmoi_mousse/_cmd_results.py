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
class ParsedConfig:
    dest_dir: Path = Path.home()
    git_auto_add: bool = False
    git_auto_commit: bool = False
    git_auto_push: bool = False


@dataclass(slots=True)
class ParsedPaths:
    managed_dirs: list[Path] = field(default_factory=list[Path])
    managed_files: list[Path] = field(default_factory=list[Path])
    x_dirs_with_status_children: set[Path] = field(default_factory=lambda: set())
    tree_x_dirs: list[Path] = field(default_factory=lambda: [])
    real_x_dirs: list[Path] = field(default_factory=lambda: [])
    real_x_files: list[Path] = field(default_factory=lambda: [])
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
    parsed_config: ParsedConfig = field(default_factory=ParsedConfig)
    parsed_paths: ParsedPaths = field(default_factory=ParsedPaths)
    apply_dir_nodes: dict[Path, DirNode] = field(default_factory=dict[Path, DirNode])
    re_add_dir_nodes: dict[Path, DirNode] = field(default_factory=dict[Path, DirNode])
    _status_paths: set[Path] = field(default_factory=lambda: set())

    def _on_field_change(self, name: str) -> None:
        if name != "new_results":
            return
        if self.new_results.dump_config is not None:
            self._update_dump_config(self.new_results.dump_config)
        self._update_managed_dirs_and_files()
        self._update_apply_and_re_add_status_dirs_and_files_and_status_paths()
        # Now update x dirs, x files as they depend status paths and managed dirs/files
        self._update_real_x_dirs_and_files()
        # Now update dirs with and without status children as they also depend on
        # status paths and managed dirs/files
        self._update_dirs_with_and_dirs_without_status_children()
        # Now update dir nodes as they depend on all of the above
        self._update_apply_and_re_add_dir_nodes()

    def _update_dump_config(self, dump_config_result: CommandResult) -> None:
        parsed_config = json.loads(dump_config_result.completed_process.stdout)
        self.parsed_config = ParsedConfig(
            dest_dir=Path(parsed_config["destDir"]),
            git_auto_add=parsed_config["git"]["autoadd"],
            git_auto_commit=parsed_config["git"]["autocommit"],
            git_auto_push=parsed_config["git"]["autopush"],
        )

    def _update_managed_dirs_and_files(self) -> None:
        if (
            self.new_results.managed_dirs is None
            or self.new_results.managed_files is None
        ):
            raise ValueError(
                "One of the required CommandResults is None. Cannot update."
            )
        self.parsed_paths.managed_dirs = [self.parsed_config.dest_dir] + [
            Path(line) for line in self.new_results.managed_dirs.std_out.splitlines()
        ]
        self.parsed_paths.managed_files = [
            Path(line) for line in self.new_results.managed_files.std_out.splitlines()
        ]

    def _update_apply_and_re_add_status_dirs_and_files_and_status_paths(self) -> None:
        def get_all_status_paths(status_lines: list[str]) -> set[Path]:
            all_status_paths: set[Path] = set()
            for line in status_lines:
                all_status_paths.add(Path(line[3:]))
            return all_status_paths

        def parse_status_output(
            status_results: "CommandResult", index: int
        ) -> dict[Path, StatusCode]:
            status_dict: dict[Path, StatusCode] = {}
            for line in status_results.std_out.splitlines():
                parsed_path = Path(line[3:])
                status_dict[parsed_path] = StatusCode(line[index])
            return status_dict

        if (
            self.new_results.status_dirs is None
            or self.new_results.status_files is None
        ):
            raise ValueError(
                "One of the required CommandResults is None. Cannot update."
            )

        # Update status paths
        self._status_paths = get_all_status_paths(
            self.new_results.status_dirs.std_out.splitlines()
            + self.new_results.status_files.std_out.splitlines()
        )

        # Update apply status dirs and files
        self.parsed_paths.apply_status_dirs = parse_status_output(
            self.new_results.status_dirs, index=0
        )
        self.parsed_paths.apply_status_files = parse_status_output(
            self.new_results.status_files, index=0
        )
        # Update re-add status dirs and files
        self.parsed_paths.re_add_status_dirs = parse_status_output(
            self.new_results.status_dirs, index=1
        )
        self.parsed_paths.re_add_status_files = parse_status_output(
            self.new_results.status_files, index=1
        )

    def _update_real_x_dirs_and_files(self) -> None:
        self.parsed_paths.real_x_dirs = [
            path
            for path in self.parsed_paths.managed_dirs
            if path not in self._status_paths
        ]
        self.parsed_paths.real_x_files = [
            path
            for path in self.parsed_paths.managed_files
            if path not in self._status_paths
        ]

    def _update_dirs_with_and_dirs_without_status_children(self) -> None:
        # Update dirs with status children for tree population logic
        self.parsed_paths.x_dirs_with_status_children = set()
        for path in self._status_paths:
            current = path.parent
            while current != current.parent:
                self.parsed_paths.x_dirs_with_status_children.add(current)
                current = current.parent
        # Update dirs without status children for tree population logic
        self.parsed_paths.tree_x_dirs = [
            d
            for d in self.parsed_paths.managed_dirs
            if d not in self.parsed_paths.x_dirs_with_status_children
        ]

    def _update_apply_and_re_add_dir_nodes(self) -> None:
        def get_x_files_in(dir_path: Path) -> dict[Path, StatusCode]:
            # x files are the same for apply and re_add contexts
            return {
                path: StatusCode.No_Status
                for path in self.parsed_paths.managed_files
                if path.parent == dir_path and path not in self._status_paths
            }

        def get_real_x_dirs_in(dir_path: Path) -> dict[Path, StatusCode]:
            # x dirs are the same for apply and re_add contexts
            return {
                path: StatusCode.No_Status
                for path in self.parsed_paths.managed_dirs
                if path.parent == dir_path and path not in self._status_paths
            }

        def get_tree_x_dirs_in(dir_path: Path) -> dict[Path, StatusCode]:
            return {
                path: StatusCode.No_Status
                for path in self.parsed_paths.managed_dirs
                if path.parent == dir_path
                and path not in self._status_paths
                and path not in self.parsed_paths.x_dirs_with_status_children
            }

        def get_tree_status_dirs_in(
            sub_dir_paths: list[Path], status_dirs: dict[Path, StatusCode]
        ) -> dict[Path, StatusCode]:
            result: dict[Path, StatusCode] = {}
            for sub_dir in sub_dir_paths:
                if sub_dir in status_dirs:
                    result[sub_dir] = status_dirs[sub_dir]
                elif sub_dir in self.parsed_paths.x_dirs_with_status_children:
                    result[sub_dir] = StatusCode.No_Status
            return dict(sorted(result.items()))

        def get_nested_status_dirs_in(
            dir_path: Path, status_dirs: dict[Path, StatusCode]
        ) -> dict[Path, StatusCode]:
            return {
                path: status
                for path, status in status_dirs.items()
                if path.is_relative_to(dir_path)
                and len(path.relative_to(dir_path).parts) > 1
            }

        def get_nested_status_files_in(
            dir_path: Path, status_files: dict[Path, StatusCode]
        ) -> dict[Path, StatusCode]:
            return {
                path: status
                for path, status in status_files.items()
                if path.is_relative_to(dir_path)
                and len(path.relative_to(dir_path).parts) > 1
            }

        for dir_path in self.parsed_paths.managed_dirs:
            sub_dir_paths = [
                p for p in self.parsed_paths.managed_dirs if p.parent == dir_path
            ]
            # Update apply nodes
            apply_dir_status = self.parsed_paths.apply_status_dirs.get(
                dir_path, StatusCode.No_Status
            )
            apply_status_files_in = {
                path: status
                for path, status in self.parsed_paths.apply_status_files.items()
                if path.parent == dir_path
            }
            apply_status_dirs_in = {
                path: status
                for path, status in self.parsed_paths.apply_status_dirs.items()
                if path.parent == dir_path
            }
            self.apply_dir_nodes[dir_path] = DirNode(
                dir_status=apply_dir_status,
                status_files_in=apply_status_files_in,
                x_files_in=get_x_files_in(dir_path),
                real_status_dirs_in=apply_status_dirs_in,
                tree_status_dirs_in=get_tree_status_dirs_in(
                    sub_dir_paths, apply_status_dirs_in
                ),
                tree_x_dirs_in=get_tree_x_dirs_in(dir_path),
                real_x_dirs_in=get_real_x_dirs_in(dir_path),
                nested_status_dirs=get_nested_status_dirs_in(
                    dir_path, self.parsed_paths.apply_status_dirs
                ),
                nested_status_files=get_nested_status_files_in(
                    dir_path, self.parsed_paths.apply_status_files
                ),
            )

            # Update re-add nodes
            re_add_dir_status = self.parsed_paths.re_add_status_dirs.get(
                dir_path, StatusCode.No_Status
            )
            re_add_status_files_in = {
                path: status
                for path, status in self.parsed_paths.re_add_status_files.items()
                if path.parent == dir_path
            }
            re_add_status_dirs_in = {
                path: status
                for path, status in self.parsed_paths.re_add_status_dirs.items()
                if path.parent == dir_path
            }
            self.re_add_dir_nodes[dir_path] = DirNode(
                dir_status=re_add_dir_status,
                status_files_in=re_add_status_files_in,
                x_files_in=get_x_files_in(dir_path),
                real_status_dirs_in=re_add_status_dirs_in,
                tree_status_dirs_in=get_tree_status_dirs_in(
                    sub_dir_paths, re_add_status_dirs_in
                ),
                tree_x_dirs_in=get_tree_x_dirs_in(dir_path),
                real_x_dirs_in=get_real_x_dirs_in(dir_path),
                nested_status_dirs=get_nested_status_dirs_in(
                    dir_path, self.parsed_paths.re_add_status_dirs
                ),
                nested_status_files=get_nested_status_files_in(
                    dir_path, self.parsed_paths.re_add_status_files
                ),
            )
