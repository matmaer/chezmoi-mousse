from typing import TYPE_CHECKING

from textual import getters, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import Collapsible, Label, Static

from chezmoi_mousse import OpBtnEnum, OperateString, Tcss

from .actionables import OpButton
from .loggers import CmdResultCollapsible

if TYPE_CHECKING:
    from chezmoi_mousse import ChezmoiGui

__all__ = ["CommandOutput", "OpFeedBack", "OperateInfo"]


class OperateInfo(Static):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    changes_enabled: reactive[bool] = reactive(False, init=False)
    current_button: OpButton | None = None

    def on_mount(self) -> None:
        self.display = False

    def update_review_info(self, button: OpButton) -> None:
        self.current_button = button
        info_lines: list[str] = []
        info_lines.append(
            self.app.cm_gui.run_cmd.review_cmd(
                verb_cmd=button.btn_enum.write_cmd, path_arg=button.btn_enum.path_arg
            )
        )
        info_lines.append(button.btn_enum.op_info_string)
        if button.btn_enum != OpBtnEnum.apply_review:
            if self.app.cm_gui.cfg.auto_commit is True:
                info_lines.append(OperateString.auto_commit)
            if self.app.cm_gui.cfg.auto_push is True:
                info_lines.append(OperateString.auto_push)
        else:
            info_lines.append(
                "[dim]Apply operation: auto-commit and auto-push not applicable[/]"
            )
        self.update("\n".join(info_lines))
        self.border_title = button.btn_enum.op_info_title
        self.border_subtitle = button.btn_enum.op_info_subtitle

    def watch_changes_enabled(self) -> None:
        if not self.display or self.current_button is None:
            return
        self.update_review_info(self.current_button)


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
        if self.app.cm_gui.added_paths:
            self.added_paths.update(
                "\n".join([str(p) for p in self.app.cm_gui.added_paths])
            )
        else:
            self.added_paths.update("No added paths")
        if self.app.cm_gui.removed_paths:
            self.removed_paths.update(
                "\n".join([str(p) for p in self.app.cm_gui.removed_paths])
            )
        else:
            self.removed_paths.update("No removed paths")
        if self.app.cm_gui.changed_status_paths:
            self.changed_status.update(
                "\n".join([str(p) for p in self.app.cm_gui.changed_status_paths])
            )
        else:
            self.changed_status.update("No changed status paths")
        # mount a collapsible for each command
        for result in self.app.cm_gui.loading_modal_results:
            self.mount(CmdResultCollapsible(cmd_result=result))


class OpFeedBack(Vertical):

    def compose(self) -> ComposeResult:
        yield OperateInfo(classes=Tcss.operate_info)
        yield CommandOutput()

    def on_mount(self) -> None:
        self.display = False
