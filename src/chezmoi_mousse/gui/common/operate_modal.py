from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual import getters, on, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical, VerticalGroup
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Label, LoadingIndicator, Static

from chezmoi_mousse.cmd_results import CmdResults
from chezmoi_mousse.functions import AppLife, Commands, min_wait
from chezmoi_mousse.str_enums import (
    LoadingLabel,
    OpBtnLabel,
    OpInfoString,
    ReadCmd,
    SectionLabel,
    Tcss,
    WriteCmd,
)

from .actionables import ExitModalBtn, ReviewBtn, RunBtn, RunBtnGroup
from .components import MainSectionLabel, SubSectionLabel

if TYPE_CHECKING:
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

__all__ = ["LoadingModal", "OperateModal"]


class LoadingModal(ModalScreen[None]):
    """
    A modal screen that displays a loading indicator and a label.
    The screen does not dismiss on its own, and must be dismissed by the parent screen.
    """

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    label_text: reactive[str | None] = reactive(None)

    def compose(self) -> ComposeResult:
        yield (VerticalGroup(Label(LoadingLabel.loading), LoadingIndicator()))

    @work
    async def run_write_command(self, write_cmd: WriteCmd, path_arg: Path) -> None:
        await self._run_write_command(write_cmd, path_arg).wait()
        await self.run_managed_commands().wait()

    @work
    async def run_managed_commands(self) -> None:
        for cmd in ReadCmd.managed_commands():
            self.label_text = f"Running: {AppLife.pretty_cmd(cmd, path=None)}"
            await self._run_read_command(cmd).wait()

    @work(thread=True)
    @min_wait
    async def _run_read_command(self, read_cmd: ReadCmd) -> None:
        Commands.run_read_cmd(read_cmd, path_arg=None)

    @work(thread=True)
    @min_wait
    async def _run_write_command(self, write_cmd: WriteCmd, path_arg: Path) -> None:
        Commands.run_write_cmd(
            write_cmd,
            path_arg=path_arg,
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
        yield MainSectionLabel(SectionLabel.changed_paths)
        yield SubSectionLabel(SectionLabel.added_managed_paths)
        yield self.AddedManaged(classes=Tcss.info)
        yield SubSectionLabel(SectionLabel.removed_managed_paths)
        yield self.RemovedManaged(classes=Tcss.info)
        yield SubSectionLabel(SectionLabel.changed_status_paths)
        yield self.ChangedStatus(classes=Tcss.info)
        yield SubSectionLabel(SectionLabel.command_outputs)

    def on_mount(self) -> None:
        self.added_managed = self.query_exactly_one(self.AddedManaged)
        self.removed_managed = self.query_exactly_one(self.RemovedManaged)
        self.changed_status = self.query_exactly_one(self.ChangedStatus)
        if not CmdResults.changed_paths.added_managed:
            self.added_managed.update("No added managed paths")
        if not CmdResults.changed_paths.removed_managed:
            self.removed_managed.update("No removed managed paths")
        if not CmdResults.changed_paths.changed_status:
            self.changed_status.update("No changed status paths")
        if CmdResults.changed_paths.added_managed:
            self.added_managed.update(CmdResults.changed_paths.added_managed_str)
        if CmdResults.changed_paths.removed_managed:
            self.removed_managed.update(CmdResults.changed_paths.removed_managed_str)
        if CmdResults.changed_paths.changed_status:
            self.changed_status.update(CmdResults.changed_paths.changed_status_str)


class OperateModal(ModalScreen[None]):
    def __init__(self, labels: tuple[OpBtnLabel, ...]) -> None:
        self.labels = labels
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield OperateInfo()
            yield CommandOutput()
            yield RunBtnGroup(self.labels)

    def on_mount(self) -> None:
        operate_info = self.query_exactly_one(OperateInfo)
        if len(self.labels) == 1 and self.labels[0] == OpBtnLabel.close:
            # condition after a refresh trees operation
            operate_info.display = False

    @on(RunBtn.Pressed)
    def handle_run_button(self, event: RunBtn.Pressed) -> None:
        self.notify(f"btn pressed {event.button}")

    @on(ExitModalBtn.Pressed)
    def handle_exit_modal(self, event: ExitModalBtn.Pressed) -> None:
        self.notify(f"btn pressed {event.button}")
