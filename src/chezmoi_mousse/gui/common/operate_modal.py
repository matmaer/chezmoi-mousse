from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual import getters, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical, VerticalGroup
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Collapsible, Label, LoadingIndicator, Static

from chezmoi_mousse.dataclass_types import ReviewBtnData
from chezmoi_mousse.functions import AppLife, Commands, min_wait
from chezmoi_mousse.str_enums import (
    LoadingLabel,
    OpBtnLabel,
    OpInfoString,
    ReadCmd,
    Tcss,
    WriteCmd,
)

from .actionables import ReviewButton, RunBtnGroup

if TYPE_CHECKING:
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

__all__ = ["LoadingModal", "OperateModal"]


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
            yield Label(LoadingLabel.loading)
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


class OperateInfo(Static):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    dry_run: reactive[bool] = reactive(False)
    current_button: ReviewButton

    def __init__(self) -> None:
        self.current_command: WriteCmd | None = None
        super().__init__(classes=Tcss.operate_info)

    def on_mount(self) -> None:
        self.display = False

    def _update_review_info(self, button: ReviewButton, dry_run: bool) -> None:
        self.current_button = button
        info_lines: list[str] = []
        # TODO: append pretty cmd
        info_lines.append(f"Will run command with dry run {dry_run}")
        info_lines.append(button.bd.op_info_string)
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
        self.border_subtitle = button.bd.op_info_subtitle

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
        self._reset_widgets()

    @work
    async def _reset_widgets(self) -> None:
        self.added_managed.update("")
        self.removed_managed.update("")
        self.changed_status.update("")
        self.query_children(Collapsible).remove()


class OperateModal(ModalScreen[None]):
    def __init__(self, review_btn: ReviewButton | None) -> None:
        self.review_btn = review_btn
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Vertical(OperateInfo(), CommandOutput(), RunBtnGroup(self.review_btn))
