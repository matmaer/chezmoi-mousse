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

from .actionables import RunBtnGroup
from .components import MainSectionLabel, SubSectionLabel
from .messages import ExitModalBtnMsg

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

    live_run: reactive[bool] = reactive(False)

    def __init__(self, btn_label: OpBtnLabel) -> None:
        self.btn_label = btn_label
        super().__init__(classes=Tcss.operate_info)

    def on_mount(self) -> None:
        self._update_review_info()

    def _update_review_info(self) -> None:
        info_lines: list[str] = []
        if self.live_run is False:
            info_lines.append(OpInfoString.dry_run_notice)
        else:
            info_lines.append(OpInfoString.live_run_notice)
        if self.btn_label is not OpBtnLabel.apply_run:
            if self.app.cmattr.auto_add is True:
                info_lines.append(OpInfoString.auto_add)
            if self.app.cmattr.auto_commit is True:
                info_lines.append(OpInfoString.auto_commit)
            if self.app.cmattr.auto_push is True:
                info_lines.append(OpInfoString.auto_push)
        else:
            info_lines.append(OpInfoString.auto_settings_not_applicable)
        self.update("\n".join(info_lines))
        self.border_title = OpInfoString.ready_to_run_title

    def watch_dry_run(self) -> None:
        if not self.display:
            return
        self._update_review_info()


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
        self.operate_label = next(
            label for label in self.labels if label in OpBtnLabel.run_btn_set()
        )
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield OperateInfo(self.operate_label)
            yield CommandOutput()
            yield RunBtnGroup(self.labels)

    def on_mount(self) -> None:
        operate_info = self.query_exactly_one(OperateInfo)
        command_output = self.query_exactly_one(CommandOutput)
        if len(self.labels) == 1 and self.labels[0] == OpBtnLabel.close:
            # condition after a refresh trees operation
            operate_info.display = False
        else:
            command_output.display = False

    @on(ExitModalBtnMsg)
    def _handle_exit_modal(self, event: ExitModalBtnMsg) -> None:
        event.stop()
        self.dismiss()
