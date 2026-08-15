from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from textual import getters, work
from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Label, LoadingIndicator

from chezmoi_mousse.cm_command import ReadCmd
from chezmoi_mousse.enum_data import OpBtnEnum
from chezmoi_mousse.functions import Commands, min_wait
from chezmoi_mousse.named_tuples import CommandResult
from chezmoi_mousse.str_enums import ColorVar

from .actionables import RefreshTreeButton

if TYPE_CHECKING:
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

__all__ = ["LoadingLabel", "LoadingModal"]


class LoadingLabel(StrEnum):
    loading = "Loading"  # the initial label
    log_cmd_results = "Logging command results"
    purge_cache = "Purge cached data"
    update_trees = "Update Trees"

    @property
    def with_color(self) -> str:
        return f"[${ColorVar.text}]{self.value}[/]"


class LoadingModal(ModalScreen[list[CommandResult]]):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    label_text: reactive[str] = reactive("Loading...")

    def __init__(self, *, btn_data: OpBtnEnum | RefreshTreeButton | None) -> None:
        self.btn_data = btn_data
        super().__init__()

    def compose(self) -> ComposeResult:
        with VerticalGroup():
            yield Label(LoadingLabel.loading.with_color)
            yield LoadingIndicator()

    def on_mount(self) -> None:
        self.command_results: list[CommandResult] = []
        self.app.cmattr.changes.clear_changes()

    def watch_label_text(self, label_text: str | None) -> None:
        if label_text is None:
            return
        label = self.query_exactly_one(Label)
        label.update(label_text)

    @work
    async def run_managed_commands(self) -> None:
        for read_cmd in self.app.cmattr.read_cmd_groups.managed:
            await self._run_read_command(read_cmd).wait()

    @work
    async def run_write_command(self, btn_enum: OpBtnEnum) -> None:
        await self._run_write_command(btn_enum).wait()
        await self.run_managed_commands().wait()

    @work(thread=True)
    @min_wait
    async def _run_read_command(self, read_cmd: ReadCmd) -> None:
        self.command_results.append(Commands.run_read_cmd(read_cmd))

    @work(thread=True)
    @min_wait
    async def _run_write_command(self, btn_enum: OpBtnEnum) -> None:
        self.command_results.append(
            Commands.run_write_cmd(
                btn_enum.write_cmd,
                dry_run=self.app.cmattr.dry_run,
                path_arg=btn_enum.path_arg,
            )
        )
