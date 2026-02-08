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
                self._on_field_change(name, old_value, value)
        else:
            super().__setattr__(name, value)

    def _on_field_change(self, name: str, old_value: Any, new_value: Any) -> None:
        # Override in subclasses to define update logic
        pass


@dataclass(slots=True)
class CmdResults(ReactiveDataclass):
    cat_config_results: "CommandResult | None" = None
    doctor_results: "CommandResult | None" = None
    dump_config_results: "CommandResult | None" = None
    git_log_results: "CommandResult | None" = None
    ignored_results: "CommandResult | None" = None
    managed_dirs_results: "CommandResult | None" = None
    managed_files_results: "CommandResult | None" = None
    status_dirs_results: "CommandResult | None" = None
    status_files_results: "CommandResult | None" = None
    template_data_results: "CommandResult | None" = None
    verify_results: "CommandResult | None" = None

    # fields updated when some_results is updated
    parsed_config: "ParsedJson | None" = None
    dest_dir: Path = field(default_factory=Path, init=False)
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

    def _on_field_change(self, name: str, old_value: Any, new_value: Any) -> None:
        if name == "managed_dirs_results" and self.managed_dirs_results is not None:
            self.managed_dirs = [
                Path(line) for line in self.managed_dirs_results.std_out.splitlines()
            ]
        if name == "managed_files_results" and self.managed_files_results is not None:
            self.managed_files = [
                Path(line) for line in self.managed_files_results.std_out.splitlines()
            ]
        if name == "status_dirs_results" and self.status_dirs_results is not None:
            self.apply_status_dirs = self._parse_status_output(
                self.status_dirs_results, index=0
            )
            self.re_add_status_dirs = self._parse_status_output(
                self.status_dirs_results, index=1
            )
        if name == "status_files_results" and self.status_files_results is not None:
            self.apply_status_files = self._parse_status_output(
                self.status_files_results, index=0
            )
            self.re_add_status_files = self._parse_status_output(
                self.status_files_results, index=1
            )
        if name == "dump_config_results" and self.dump_config_results is not None:
            self._parse_config()

    def _parse_status_output(
        self, status_results: "CommandResult", index: int
    ) -> dict[Path, StatusCode]:
        status_dict: dict[Path, StatusCode] = {}
        for line in status_results.std_out.splitlines():
            parsed_path = Path(line[3:])
            status_dict[parsed_path] = StatusCode(line[index])
        return status_dict

    def _parse_config(self) -> None:
        assert self.dump_config_results is not None
        parsed_config = json.loads(self.dump_config_results.completed_process.stdout)
        self.git_auto_add = parsed_config["git"]["autoadd"]
        self.git_auto_commit = parsed_config["git"]["autocommit"]
        self.git_auto_push = parsed_config["git"]["autopush"]
        self.dest_dir = Path(parsed_config["destDir"])
