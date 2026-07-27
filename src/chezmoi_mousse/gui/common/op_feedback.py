from __future__ import annotations

from typing import TYPE_CHECKING

from textual import getters, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import Collapsible, Label, Static

from chezmoi_mousse.cm_command import WriteCmd
from chezmoi_mousse.enum_data import OpBtnEnum, OpInfoString
from chezmoi_mousse.str_enums import Tcss

from .actionables import OpButton

if TYPE_CHECKING:
    from chezmoi_mousse.cm_types import ChezmoiGui

__all__ = ["CommandOutput", "OpFeedBack", "OperateInfo"]


class OperateInfo(Static):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    dry_run: reactive[bool] = reactive(False)
    current_button: OpButton

    def __init__(self) -> None:
        self.current_command: WriteCmd | None = None
        super().__init__(classes=Tcss.operate_info)

    def on_mount(self) -> None:
        self.display = False
        self.dest_dir = self.app.cmattr.dest_dir

    def update_review_info(self, button: OpButton, dry_run: bool) -> None:
        self.current_button = button
        info_lines: list[str] = []
        # TODO: append pretty cmd
        info_lines.append(f"Will run command with dry run {dry_run}")
        info_lines.append(button.btn_enum.op_info_string)
        if button.btn_enum != OpBtnEnum.apply_review:
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
        self.border_title = button.btn_enum.op_info_title
        self.border_subtitle = button.btn_enum.op_info_subtitle

    def watch_dry_run(self, dry_run: bool) -> None:
        if not self.display:
            return
        self.update_review_info(self.current_button, dry_run)


class CommandOutput(ScrollableContainer):

    class AddedPaths(Static): ...

    class RemovedPaths(Static): ...

    class ChangedStatusPaths(Static): ...

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def compose(self) -> ComposeResult:
        yield Label("Added paths", classes=Tcss.sub_section_label)
        yield self.AddedPaths(classes=Tcss.info)
        yield Label("Removed paths", classes=Tcss.sub_section_label)
        yield self.RemovedPaths(classes=Tcss.info)
        yield Label("Changed status paths", classes=Tcss.sub_section_label)
        yield self.ChangedStatusPaths(classes=Tcss.info)
        yield Label("Command output", classes=Tcss.main_section_label)

    def on_mount(self) -> None:
        self.added_paths = self.query_exactly_one(self.AddedPaths)
        self.removed_paths = self.query_exactly_one(self.RemovedPaths)
        self.changed_status = self.query_exactly_one(self.ChangedStatusPaths)
        self.reset_widgets()

    @work
    async def reset_widgets(self) -> None:
        self.added_paths.update("")
        self.removed_paths.update("")
        self.changed_status.update("")
        self.query_children(Collapsible).remove()

    @work
    async def update_cmd_output(self) -> None:
        if self.app.cmattr.changes.added_paths:
            self.added_paths.update(
                "\n".join([str(p) for p in self.app.cmattr.changes.added_paths])
            )
        else:
            self.added_paths.update("No added paths")
        if self.app.cmattr.changes.removed_paths:
            self.removed_paths.update(
                "\n".join([str(p) for p in self.app.cmattr.changes.removed_paths])
            )
        else:
            self.removed_paths.update("No removed paths")
        if self.app.cmattr.changes.changed_status_paths:
            self.changed_status.update(
                "\n".join(
                    [str(p) for p in self.app.cmattr.changes.changed_status_paths]
                )
            )
        else:
            self.changed_status.update("No changed status paths")


class OpFeedBack(Vertical):

    def compose(self) -> ComposeResult:
        yield OperateInfo()
        yield CommandOutput()

    def on_mount(self) -> None:
        self.display = False
