from __future__ import annotations

import json
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._str_enums import StatusCode

if TYPE_CHECKING:
    from ._chezmoi_command import CommandResult

type ParsedJson = dict[str, Any]

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
    cat_config_results: CommandResult | None = None
    doctor_results: CommandResult | None = None
    dump_config_results: CommandResult | None = None
    git_log_results: CommandResult | None = None
    ignored_results: CommandResult | None = None
    managed_dirs_results: CommandResult | None = None
    managed_files_results: CommandResult | None = None
    status_dirs_results: CommandResult | None = None
    status_files_results: CommandResult | None = None
    template_data_results: CommandResult | None = None
    verify_results: CommandResult | None = None
    changed_paths: ChangedPaths = field(default_factory=ChangedPaths)

    # fields updated when some_results is updated
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

    @property
    def executed_commands(self) -> list["CommandResult"]:
        return [
            getattr(self, field.name)
            for field in fields(self)
            if field.name.endswith("_results")
        ]

    @property
    def status_dirs(self) -> set[Path]:
        return set(self.apply_status_dirs.keys()) | set(self.re_add_status_dirs.keys())

    def _on_field_change(self, name: str) -> None:
        if name == "managed_dirs_results" and self.managed_dirs_results is not None:
            old_dirs = self.managed_dirs
            new_dirs = [
                Path(line) for line in self.managed_dirs_results.std_out.splitlines()
            ]
            self.changed_paths.added_managed_dirs = [
                d for d in new_dirs if d not in old_dirs
            ]
            self.changed_paths.removed_managed_dirs = [
                d for d in old_dirs if d not in new_dirs
            ]
            self.managed_dirs = new_dirs
        if name == "managed_files_results" and self.managed_files_results is not None:
            old_files = self.managed_files
            new_files = [
                Path(line) for line in self.managed_files_results.std_out.splitlines()
            ]
            self.changed_paths.added_managed_files = [
                f for f in new_files if f not in old_files
            ]
            self.changed_paths.removed_managed_files = [
                f for f in old_files if f not in new_files
            ]
            self.managed_files = new_files
        if name == "status_dirs_results" and self.status_dirs_results is not None:
            old_apply = self.apply_status_dirs
            old_re_add = self.re_add_status_dirs
            new_apply = self._parse_status_output(self.status_dirs_results, index=0)
            new_re_add = self._parse_status_output(self.status_dirs_results, index=1)
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
        if name == "status_files_results" and self.status_files_results is not None:
            old_apply = self.apply_status_files
            old_re_add = self.re_add_status_files
            new_apply = self._parse_status_output(self.status_files_results, index=0)
            new_re_add = self._parse_status_output(self.status_files_results, index=1)
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
            self.changed_re_add_status_files = changed_re_add
            self.apply_status_files = new_apply
            self.re_add_status_files = new_re_add
        if name == "dump_config_results" and self.dump_config_results is not None:
            parsed_config = json.loads(
                self.dump_config_results.completed_process.stdout
            )
            self.git_auto_add = parsed_config["git"]["autoadd"]
            self.git_auto_commit = parsed_config["git"]["autocommit"]
            self.git_auto_push = parsed_config["git"]["autopush"]
            self.dest_dir = Path(parsed_config["destDir"])

    def _parse_status_output(
        self, status_results: "CommandResult", index: int
    ) -> dict[Path, StatusCode]:
        status_dict: dict[Path, StatusCode] = {}
        for line in status_results.std_out.splitlines():
            parsed_path = Path(line[3:])
            status_dict[parsed_path] = StatusCode(line[index])
        return status_dict
