from dataclasses import dataclass, fields

from ._app_ids import CanvasIds
from ._chezmoi_command import ChezmoiCommand, CommandResult

__all__ = ["CMD", "CMD_RESULTS", "IDS", "CommandResults"]


CMD = ChezmoiCommand()
IDS = CanvasIds()


@dataclass(slots=True)
class CommandResults:
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

    @property
    def executed_commands(self) -> list["CommandResult"]:
        return [
            getattr(self, field.name)
            for field in fields(self)
            if getattr(self, field.name) is not None
        ]


CMD_RESULTS = CommandResults()
