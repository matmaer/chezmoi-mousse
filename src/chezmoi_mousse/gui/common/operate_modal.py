from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual import getters, on, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical, VerticalGroup
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Label, LoadingIndicator, Static

from chezmoi_mousse.functions import AppLife, Commands, min_wait
from chezmoi_mousse.str_enums import (
    LoadingLabel,
    OpBtnLabel,
    OpInfoString,
    ReadCmd,
    Tcss,
    WriteCmd,
)

from .actionables import (
    ExitModalBtn,
    RefreshBtn,
    ReviewBtn,
    RunBtn,
)

if TYPE_CHECKING:
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

__all__ = ["LoadingModal", "OperateModal"]


class LoadingModal(ModalScreen[None]):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    label_text: reactive[str | None] = reactive(None)

    def __init__(
        self,
        *,
        operation: WriteCmd | RefreshBtn | None,
        path_arg: Path | None,
        dry_run: bool | None = None,
    ) -> None:
        self.operation = operation
        self.path_arg = path_arg
        self.dry_run = dry_run
        super().__init__()

    def compose(self) -> ComposeResult:
        yield (VerticalGroup(Label(LoadingLabel.loading), LoadingIndicator()))

    def on_mount(self) -> None:
        if self.operation is None:
            return
        self._dispatch_commands()

    def _take_managed_snapshot(self) -> None: ...

    @work
    async def _dispatch_commands(self) -> None:
        if isinstance(self.operation, RefreshBtn):
            await self.run_managed_commands().wait()
        elif isinstance(self.operation, WriteCmd):
            await self._run_write_command(self.operation).wait()
            await self.run_managed_commands().wait()

    @work
    async def run_managed_commands(self) -> None:
        for cmd in ReadCmd.managed_commands():
            self.label_text = f"Running: {AppLife.pretty_cmd(cmd, dry=None, path=None)}"
            await self._run_read_command(cmd).wait()

    @work(thread=True)
    @min_wait
    async def _run_read_command(self, read_cmd: ReadCmd) -> None:
        Commands.run_read_cmd(read_cmd, path_arg=None)

    @work(thread=True)
    @min_wait
    async def _run_write_command(self, write_cmd: WriteCmd) -> None:
        Commands.run_write_cmd(
            write_cmd,
            dry_run=self.app.cmattr.dry_run,
            path_arg=self.path_arg,
        )

    def watch_label_text(self, label_text: str) -> None:
        if self.label_text is None:
            return
        label = self.query_exactly_one(Label)
        label.update(label_text)


class OperateInfo(Static):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    dry_run: reactive[bool] = reactive(False)
    current_button: ReviewBtn

    def __init__(self) -> None:
        self.current_command: WriteCmd | None = None
        super().__init__(classes=Tcss.operate_info)

    def on_mount(self) -> None:
        self.display = False

    def _update_review_info(self, button: ReviewBtn, dry_run: bool) -> None:
        self.current_button = button
        info_lines: list[str] = []
        # TODO: append pretty cmd
        info_lines.append(f"Will run command with dry run {dry_run}")
        if button.label is not OpBtnLabel.apply_review:
            if self.app.cmattr.auto_add is True:
                info_lines.append(OpInfoString.auto_commit)
            if self.app.cmattr.auto_commit is True:
                info_lines.append(OpInfoString.auto_commit)
            if self.app.cmattr.auto_push is True:
                info_lines.append(OpInfoString.auto_push)
        else:
            msg = (
                "[dim]Apply operation: chezmoi autoadd, autocommit and autopush not "
                "applicable[/]"
            )
            info_lines.append(msg)
        self.update("\n".join(info_lines))
        self.border_title = OpInfoString.ready_to_run

    def watch_dry_run(self, dry_run: bool) -> None:
        if not self.display:
            return
        self._update_review_info(self.current_button, dry_run)


class CommandOutput(ScrollableContainer):
    class AddedManaged(Static): ...

    class RemovedManaged(Static): ...

    class ChangedStatus(Static): ...

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def compose(self) -> ComposeResult:
        yield Label("Added managed paths", classes=Tcss.sub_section_label)
        yield self.AddedManaged(classes=Tcss.info)
        yield Label("Removed managed paths", classes=Tcss.sub_section_label)
        yield self.RemovedManaged(classes=Tcss.info)
        yield Label("Changed status paths", classes=Tcss.sub_section_label)
        yield self.ChangedStatus(classes=Tcss.info)
        yield Label("Command output", classes=Tcss.main_section_label)

    def on_mount(self) -> None:
        self.added_managed = self.query_exactly_one(self.AddedManaged)
        self.removed_managed = self.query_exactly_one(self.RemovedManaged)
        self.changed_status = self.query_exactly_one(self.ChangedStatus)


class OperateModal(ModalScreen[None]):
    def __init__(self, labels: tuple[OpBtnLabel, ...]) -> None:
        self.labels = labels
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield OperateInfo()
            yield CommandOutput()

    def on_mount(self) -> None:
        cmd_output = self.query_exactly_one(CommandOutput)
        cmd_output.display = False

    @on(RunBtn.Pressed)
    def handle_run_button(self, event: RunBtn.Pressed) -> None:
        self.notify(f"btn pressed {event.button}")

    @on(ExitModalBtn.Pressed)
    def handle_exit_modal(self, event: ExitModalBtn.Pressed) -> None:
        self.notify(f"btn pressed {event.button}")
