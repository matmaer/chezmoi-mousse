from typing import TYPE_CHECKING

from textual import work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import Label, Static

from chezmoi_mousse import CMD, AppType, OpBtnEnum, OperateString, OpInfoString, Tcss

from .actionables import OpButton

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["CommandOutput", "OpFeedBack", "OperateInfo"]


class OperateInfo(Static, AppType):

    changes_enabled: reactive[bool] = reactive(False, init=False)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.static.operate_info, classes=Tcss.operate_info)
        self.current_button: OpButton | None = None

    def on_mount(self) -> None:
        self.display = False

    def update_review_info(self, button: OpButton) -> None:
        self.current_button = button
        info_lines: list[str] = []
        info_lines.append(
            CMD.run_cmd.review_cmd(
                verb_cmd=button.btn_enum.write_cmd, path_arg=button.btn_enum.path_arg
            )
        )
        info_lines.append(button.btn_enum.op_info_string)
        if button.btn_enum != OpBtnEnum.apply_review:
            if CMD.cache.git_auto_commit is True:
                info_lines.append(OperateString.auto_commit)
            if CMD.cache.git_auto_push is True:
                info_lines.append(OperateString.auto_push)
        else:
            info_lines.append(
                "[dim]Apply operation: auto-commit and auto-push not applicable[/]"
            )
        self.update("\n".join(info_lines))
        self.border_title = button.btn_enum.op_info_title
        self.border_subtitle = button.btn_enum.op_info_subtitle

    @work
    async def update_write_cmd_info(self) -> None:
        self.update(
            f"{CMD.loading_modal_results[0].exit_code_colored_cmd}\n"
            f"Exit code {CMD.loading_modal_results[0].exit_code}"
        )
        self.border_title = OpInfoString.command_completed
        self.border_subtitle = None

    def watch_changes_enabled(self) -> None:
        if not self.display or self.current_button is None:
            return
        self.update_review_info(self.current_button)


class CommandOutput(ScrollableContainer):

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.command_output)
        self.ids = ids

    def compose(self) -> ComposeResult:
        yield Label("Changed paths", classes=Tcss.main_section_label)
        yield Static(id=self.ids.static.changed_paths, classes=Tcss.info)
        yield Label("Command output", classes=Tcss.main_section_label)

    def on_mount(self) -> None:
        self.changed_paths_static = self.query_one(
            self.ids.static.changed_paths_q, Static
        )

    @work
    async def update_mounted(self) -> None:
        if not CMD.changed_paths:
            dry_run = (
                " (dry run)"
                if any(
                    cmd_result.is_dry_run for cmd_result in CMD.loading_modal_results
                )
                else ""
            )
            self.changed_paths_static.update(f"No paths changed.{dry_run}")
        else:
            changed_paths_strings = "\n".join(str(path) for path in CMD.changed_paths)
            self.changed_paths_static.update(changed_paths_strings)
        for cmd_result in CMD.loading_modal_results:
            self.mount(cmd_result.pretty_collapsible)


class OpFeedBack(Vertical):

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.op_feed_back)
        self.ids = ids

    def compose(self) -> ComposeResult:
        yield OperateInfo(self.ids)
        yield CommandOutput(self.ids)

    def on_mount(self) -> None:
        self.display = False
