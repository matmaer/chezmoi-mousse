from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalGroup
from textual.events import Click
from textual.screen import ModalScreen
from textual.widgets import Button, Collapsible

from chezmoi_mousse.chezmoi import chezmoi, chezmoi_config, cmd_log, op_log
from chezmoi_mousse.constants import ModalIdStr, OperateVerbs, TcssStr
from chezmoi_mousse.containers import ButtonsHorizontal
from chezmoi_mousse.id_typing import (
    Location,
    OperateBtn,
    OperateButtons,
    OperateData,
    TabIds,
    TabStr,
    ViewStr,
)
from chezmoi_mousse.messages import OperateMessage
from chezmoi_mousse.widgets import (
    ContentsView,
    DiffView,
    GitLogView,
    OperateInfo,
)

# import json
# import sys
# from pathlib import Path
# from shutil import which
# from subprocess import run

# from .id_typing import ParsedJson

# if not which("chezmoi"):
#     print("Error: chezmoi command not found.", file=sys.stderr)
#     sys.exit(1)
# elif not which("git"):
#     print("Error: git command not found.", file=sys.stderr)
#     sys.exit(1)

# try:
#     chezmoi_config: ParsedJson = json.loads(
#         run(
#             BASE_CMD + ("dump-config", "--format=json"),
#             capture_output=True,
#             text=True,
#         ).stdout
#     )
# except Exception as e:
#     print(f"Failed run chezmoi dump-config: {e}", file=sys.stderr)
#     sys.exit(1)


class ModalBase(ModalScreen[None]):

    BINDINGS = [
        Binding(
            key="escape", action="esc_dismiss", description="close", show=False
        )
    ]

    def __init__(
        self, *, modal_id: ModalIdStr, path: Path | None = None
    ) -> None:
        self.modal_id = modal_id
        self.path = path
        super().__init__(id=self.modal_id.name, classes=TcssStr.modal_base)

    def on_click(self, event: Click) -> None:
        event.stop()
        if event.chain == 2 and self.modal_id != ModalIdStr.operate_modal:
            self.dismiss()

    def action_esc_dismiss(self) -> None:
        if self.modal_id != ModalIdStr.operate_modal:
            self.dismiss()


class Operate(ModalBase):

    def __init__(
        self, *, tab_ids: TabIds, path: Path, buttons: OperateButtons
    ) -> None:
        self.buttons: OperateButtons = buttons
        self.main_operate_btn = self.buttons[0]
        self.path = path
        self.tab_ids = tab_ids
        self.tab_name = tab_ids.tab_name
        self.operate_dismiss_data: OperateData = OperateData(
            path=self.path,
            operation_executed=False,
            tab_name=self.tab_ids.tab_name,
        )
        super().__init__(path=self.path, modal_id=ModalIdStr.operate_modal)

    def compose(self) -> ComposeResult:
        with Vertical(id=ModalIdStr.operate_vertical):
            yield OperateInfo(
                operate_btn=self.main_operate_btn, path=self.path
            )
            if (
                OperateBtn.apply_file == self.main_operate_btn
                or OperateBtn.re_add_file == self.main_operate_btn
            ):
                with Collapsible(
                    id=ModalIdStr.operate_collapsible, title="File Differences"
                ):
                    yield DiffView(
                        tab_name=self.tab_name,
                        view_id=ModalIdStr.modal_diff_view,
                    )
            else:
                with Collapsible(
                    id=ModalIdStr.operate_collapsible, title="File Contents"
                ):
                    yield ContentsView(view_id=ModalIdStr.modal_contents_view)
            with VerticalGroup(classes=TcssStr.operate_docked_bottom):
                yield ButtonsHorizontal(
                    tab_ids=self.tab_ids,
                    buttons=self.buttons,
                    location=Location.bottom,
                )
                yield op_log

    def on_mount(self) -> None:
        self.border_subtitle = " escape key to close "
        if (
            self.tab_name == TabStr.apply_tab
            or self.tab_name == TabStr.re_add_tab
        ) and (
            OperateBtn.apply_file in self.buttons
            or OperateBtn.re_add_file in self.buttons
        ):
            # Set path for the modal diff view
            self.query_one(ModalIdStr.modal_diff_view.qid, DiffView).path = (
                self.path
            )
        else:
            # Set path for the modal contents view
            self.query_one(
                ModalIdStr.modal_contents_view.qid, ContentsView
            ).path = self.path
        self.write_initial_log_msg()

    def write_initial_log_msg(self) -> None:
        command = "chezmoi "
        if self.buttons[0] == OperateBtn.forget_file:
            command += OperateVerbs.forget
        elif self.buttons[0] == OperateBtn.destroy_file:
            command += OperateVerbs.destroy
        elif self.tab_name == TabStr.add_tab:
            command += OperateVerbs.add
        elif self.tab_name == TabStr.apply_tab:
            command += OperateVerbs.apply
        elif self.tab_name == TabStr.re_add_tab:
            command += OperateVerbs.re_add
        cmd_log.log_ready_to_run(
            f"Ready to run command: {command} {self.path}"
        )
        op_log.log_ready_to_run(f"Ready to run command: {command} {self.path}")

    @on(Button.Pressed, ".operate_button")
    def handle_operate_buttons(self, event: Button.Pressed) -> None:
        event.stop()
        button_commands = [
            (OperateBtn.apply_file, chezmoi.perform.apply),
            (OperateBtn.re_add_file, chezmoi.perform.re_add),
            (OperateBtn.add_file, chezmoi.perform.add),
            (OperateBtn.forget_file, chezmoi.perform.forget),
            (OperateBtn.destroy_file, chezmoi.perform.destroy),
        ]
        for btn_enum, btn_cmd in button_commands:
            if event.button.id == self.tab_ids.button_id(btn_enum):
                self.query_one(
                    self.tab_ids.button_qid(OperateBtn.operate_dismiss), Button
                ).label = "Close"
                btn_cmd(self.path)  # run the perform command with the path
                self.query_one(
                    self.tab_ids.button_qid(btn_enum), Button
                ).disabled = True
                self.operate_dismiss_data.operation_executed = True
                break

        if event.button.id == self.tab_ids.button_id(
            OperateBtn.operate_dismiss
        ):
            self.handle_dismiss(self.operate_dismiss_data)

    def action_esc_dismiss(self) -> None:
        self.handle_dismiss(self.operate_dismiss_data)

    def handle_dismiss(self, dismiss_data: OperateData) -> None:
        if not dismiss_data.operation_executed and self.path:
            msg = f"Operation cancelled for {self.path.name}"
            cmd_log.log_success(msg)
            op_log.log_success(msg)
            self.notify("No changes were made")
        # send the needed data to the app, logging will be handled there
        self.app.post_message(OperateMessage(dismiss_data=dismiss_data))
        self.dismiss()


class Maximized(ModalBase):

    def __init__(
        self,
        *,
        id_to_maximize: str | None,
        path: Path | None = None,
        tab_ids: TabIds,
    ) -> None:
        self.id_to_maximize = id_to_maximize
        self.path = path
        self.tab_ids = tab_ids
        self.tab_name: TabStr = tab_ids.tab_name
        super().__init__(path=path, modal_id=ModalIdStr.maximized_modal)

    def compose(self) -> ComposeResult:
        with Vertical(id=ModalIdStr.maximized_vertical):
            if self.id_to_maximize == self.tab_ids.view_id(
                ViewStr.contents_view
            ):
                yield ContentsView(view_id=ModalIdStr.modal_contents_view)
            elif self.id_to_maximize == self.tab_ids.view_id(
                ViewStr.diff_view
            ):
                yield DiffView(
                    tab_name=self.tab_name, view_id=ModalIdStr.modal_diff_view
                )
            elif self.id_to_maximize == self.tab_ids.view_id(
                ViewStr.git_log_view
            ):
                yield GitLogView(view_id=ModalIdStr.modal_git_log_view)

    def on_mount(self) -> None:
        self.border_subtitle = " double click or escape key to close "
        if self.id_to_maximize == self.tab_ids.view_id(ViewStr.contents_view):
            self.query_one(
                ModalIdStr.modal_contents_view.qid, ContentsView
            ).path = self.path
        elif self.id_to_maximize == self.tab_ids.view_id(ViewStr.diff_view):
            self.query_one(ModalIdStr.modal_diff_view.qid, DiffView).path = (
                self.path
            )
        elif self.id_to_maximize == self.tab_ids.view_id(ViewStr.git_log_view):
            self.query_one(
                ModalIdStr.modal_git_log_view.qid, GitLogView
            ).path = self.path

        if self.path == chezmoi_config.destDir:
            self.border_title = f" {chezmoi_config.destDir} "
        elif self.path is not None:
            self.border_title = (
                f" {self.path.relative_to(chezmoi_config.destDir)} "
            )
