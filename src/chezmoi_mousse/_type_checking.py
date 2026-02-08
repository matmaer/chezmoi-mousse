from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._chezmoi_command import CommandResult, WriteCmd
    from .gui.textual_app import ChezmoiGUI

type ParsedJson = dict[str, "Any"]

__all__ = ["AppType", "CmdResults", "InitCloneData", "NodeData", "ParsedJson"]


class AppType:
    app: ChezmoiGUI


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
class CmdResults:
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
    verify: CommandResult | None = None
    # managed_dirs: list[Path] = field(default_factory=list[Path])

    @property
    def executed_commands(self) -> list[CommandResult]:
        # Return the field value which are CommandResult and not None
        return [
            getattr(self, field.name)
            for field in fields(self)
            if getattr(self, field.name) is not None
        ]

    @property
    def managed_dir_paths(self) -> list[Path]:
        if self.managed_dirs is None:
            return []
        return [Path(line) for line in self.managed_dirs.std_out.splitlines()]

    @property
    def managed_file_paths(self) -> list[Path]:
        if self.managed_files is None:
            return []
        return [Path(line) for line in self.managed_files.std_out.splitlines()]


@dataclass(slots=True)
class InitCloneData:
    init_cmd: WriteCmd
    init_arg: str
    valid_arg: bool


@dataclass(slots=True)
class NodeData:
    path: Path
