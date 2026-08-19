from __future__ import annotations

from typing import TYPE_CHECKING

from textual import getters, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Collapsible, Label, Static

from chezmoi_mousse.str_enums import OpBtnLabel, OpInfoString, Tcss, WriteCmd

from .actionables import RefreshTreeButton, ReviewButton

if TYPE_CHECKING:
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

__all__ = ["OperateModal"]


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
    def __init__(self, btn: ReviewButton | RefreshTreeButton) -> None:
        self.bnt = btn
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Vertical(OperateInfo(), CommandOutput())
