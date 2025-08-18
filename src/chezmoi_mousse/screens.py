from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalGroup
from textual.events import Click
from textual.screen import ModalScreen
from textual.widgets import Button, Collapsible

from chezmoi_mousse import CM_CFG
from chezmoi_mousse.chezmoi import OperateData, chezmoi, cmd_log, op_log
from chezmoi_mousse.containers import ButtonsHorizontal
from chezmoi_mousse.id_typing import (
    Buttons,
    Location,
    ModalIdStr,
    OperateVerbs,
    TabIds,
    TabStr,
    TcssStr,
    ViewStr,
)
from chezmoi_mousse.messages import OperateMessage
from chezmoi_mousse.widgets import (
    ContentsView,
    DiffView,
    GitLogView,
    OperateInfo,
    RichLog,
)


class ModalBase(ModalScreen[None]):

    BINDINGS = [
        Binding(
            key="escape", action="esc_dismiss", description="close", show=False
        )
    ]

    def __init__(
        self, *, tab_ids: TabIds, modal_id: ModalIdStr, path: Path
    ) -> None:
        self.path = path
        self.tab_ids = tab_ids
        super().__init__(id=modal_id, classes=TcssStr.modal_base)
        self.border_subtitle = " double click or escape key to close "

    def handle_dismiss(self, dismiss_data: OperateData) -> None:
        if not dismiss_data.operation_executed:
            msg = f"Operation cancelled for {self.path.name}"
            cmd_log.log_success(msg)
            op_log.log_success(msg)
            self.notify("No changes were made")
        # send the needed data to the app, logging will be handled there
        self.app.post_message(OperateMessage(dismiss_data=dismiss_data))
        self.dismiss()


class Operate(ModalBase):

    def __init__(
        self, *, tab_ids: TabIds, path: Path, buttons: tuple[Buttons, ...]
    ) -> None:
        self.buttons: tuple[Buttons, ...] = buttons
        self.main_operate_btn = self.buttons[0]
        self.path = path
        self.tab_ids = tab_ids
        self.tab_name = tab_ids.tab_name
        self.operate_dismiss_data: OperateData = OperateData(
            path=self.path,
            operation_executed=False,
            tab_name=self.tab_ids.tab_name,
        )
        super().__init__(
            tab_ids=self.tab_ids,
            path=self.path,
            modal_id=ModalIdStr.operate_modal,
        )

    def compose(self) -> ComposeResult:
        with Vertical(id=ModalIdStr.operate_vertical):
            yield OperateInfo(
                operate_btn=self.main_operate_btn, path=self.path
            )
            if (
                Buttons.apply_file_btn == self.main_operate_btn
                or Buttons.re_add_file_btn == self.main_operate_btn
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
            with VerticalGroup():
                yield ButtonsHorizontal(
                    tab_ids=self.tab_ids,
                    buttons=self.buttons,
                    location=Location.bottom,
                )
                yield op_log

    def on_mount(self) -> None:
        if (
            self.tab_name == TabStr.apply_tab
            or self.tab_name == TabStr.re_add_tab
        ) and (
            Buttons.apply_file_btn in self.buttons
            or Buttons.re_add_file_btn in self.buttons
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
        # Add initial log entry
        self.query_one(ModalIdStr.operate_log.qid, RichLog).border_title = (
            " Operate Log "
        )
        self.write_initial_log_msg()

    def write_initial_log_msg(self) -> None:
        command = "chezmoi "
        if self.buttons[0] == Buttons.forget_file_btn:
            command += OperateVerbs.forget.value
        elif self.buttons[0] == Buttons.destroy_file_btn:
            command += OperateVerbs.destroy.value
        elif self.tab_name == TabStr.add_tab:
            command += OperateVerbs.add.value
        elif self.tab_name == TabStr.apply_tab:
            command += OperateVerbs.apply.value
        elif self.tab_name == TabStr.re_add_tab:
            command += OperateVerbs.re_add.value
        cmd_log.log_ready_to_run(
            f"Ready to run command: {command} {self.path}"
        )
        op_log.log_ready_to_run(f"Ready to run command: {command} {self.path}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        # Refactored repeated button event handling into a loop
        button_commands = [
            (Buttons.apply_file_btn, chezmoi.perform.apply),
            (Buttons.re_add_file_btn, chezmoi.perform.re_add),
            (Buttons.add_file_btn, chezmoi.perform.add),
            (Buttons.forget_file_btn, chezmoi.perform.forget),
            (Buttons.destroy_file_btn, chezmoi.perform.destroy),
        ]
        for btn_enum, btn_cmd in button_commands:
            if event.button.id == self.tab_ids.button_id(btn_enum):
                self.query_one(
                    self.tab_ids.button_qid(Buttons.operate_dismiss_btn),
                    Button,
                ).label = "Close"
                btn_cmd(self.path)  # run the perform command with the path
                self.query_one(
                    self.tab_ids.button_qid(btn_enum), Button
                ).disabled = True
                self.operate_dismiss_data.operation_executed = True
                break

        if event.button.id == self.tab_ids.button_id(
            Buttons.operate_dismiss_btn
        ):
            self.handle_dismiss(self.operate_dismiss_data)

    def action_esc_dismiss(self) -> None:
        self.handle_dismiss(self.operate_dismiss_data)

    def on_click(self, event: Click) -> None:
        event.stop()
        if event.chain == 2:
            self.handle_dismiss(self.operate_dismiss_data)


class Maximized(ModalBase):

    def __init__(
        self, *, id_to_maximize: str | None, path: Path, tab_ids: TabIds
    ) -> None:
        self.id_to_maximize = id_to_maximize
        self.path = path
        self.tab_ids = tab_ids
        self.tab_name: TabStr = tab_ids.tab_name
        super().__init__(
            tab_ids=tab_ids, path=path, modal_id=ModalIdStr.maximized_modal
        )

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

        if self.path == CM_CFG.destDir:
            self.border_title = f" {CM_CFG.destDir} "
        else:
            self.border_title = f" {self.path.relative_to(CM_CFG.destDir)} "

    def on_click(self, event: Click) -> None:
        event.stop()
        if event.chain == 2:
            self.dismiss()

    def action_esc_dismiss(self) -> None:
        self.dismiss()
