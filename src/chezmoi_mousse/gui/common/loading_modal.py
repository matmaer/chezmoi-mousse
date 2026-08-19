from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from textual import getters, work
from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Label, LoadingIndicator

from chezmoi_mousse.dataclass_types import ReviewBtnData
from chezmoi_mousse.functions import AppLife, Commands, min_wait
from chezmoi_mousse.str_enums import ColorVar, ReadCmd, WriteCmd

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


class LoadingModal(ModalScreen[None]):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    label_text: reactive[str] = reactive("Loading...")

    def __init__(
        self,
        run_data: ReviewBtnData | None,
    ) -> None:
        self.run_data = run_data
        if run_data is None:
            self.path_arg = None
        else:
            self.path_arg = run_data.path_arg
        super().__init__()

    def compose(self) -> ComposeResult:
        with VerticalGroup():
            yield Label(LoadingLabel.loading.with_color)
            yield LoadingIndicator()

    def on_mount(self) -> None:
        self.label = self.query_exactly_one(Label)

    def _update_label(self, cmd: ReadCmd | WriteCmd, path_arg: Path | None) -> None:
        if path_arg is None:
            path = ""
        else:
            path = str(path_arg.relative_to(self.app.cmattr.dest_dir))
        label_text = "Running command:\n"
        label_text += AppLife.cmd_str_wop(cmd, dry=None, pretty=True) + f" {path}"
        self.label.update(label_text)

    @work
    async def run_managed_commands(self) -> None:
        for read_cmd in ReadCmd.managed_commands():
            self._update_label(read_cmd, None)
            await self._run_read_command(read_cmd).wait()

    @work
    async def run_write_cmd_and_managed_commands(self, run_data: ReviewBtnData) -> None:
        self._update_label(run_data.write_cmd, None)
        await self._run_write_command(run_data.write_cmd).wait()
        await self.run_managed_commands().wait()

    @work(thread=True)
    @min_wait
    async def _run_read_command(self, read_cmd: ReadCmd) -> None:
        Commands.run_read_cmd(read_cmd)

    @work(thread=True)
    @min_wait
    async def _run_write_command(self, run_data: ReviewBtnData) -> None:
        Commands.run_write_cmd(
            run_data.write_cmd,
            dry_run=self.app.cmattr.dry_run,
            path_arg=self.path_arg,
        )

    def watch_label_text(self, label_text: str) -> None:
        self.label.update(label_text)
