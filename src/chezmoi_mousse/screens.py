from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.events import Click
from textual.screen import ModalScreen
from textual.widgets import Button, Collapsible

from chezmoi_mousse import CM_CFG
from chezmoi_mousse.chezmoi import OperateData, chezmoi, cmd_log, op_log
from chezmoi_mousse.containers import ButtonsHorizontal
from chezmoi_mousse.id_typing import (
    ButtonEnum,
    CharsEnum,
    IdMixin,
    Location,
    ModalIdStr,
    OperateVerbs,
    TabStr,
    TcssStr,
    ViewStr,
)
from chezmoi_mousse.messages import OperateMessage
from chezmoi_mousse.widgets import (
    AutoWarning,
    ContentsView,
    DiffView,
    GitLogView,
    OperateInfo,
    RichLog,
)


class Operate(ModalScreen[None], IdMixin):
    BINDINGS = [
        Binding(
            key="escape", action="esc_dismiss", description="close", show=False
        )
    ]

    check_mark = CharsEnum.check_mark.value

    def __init__(
        self, tab_name: TabStr, *, path: Path, buttons: tuple[ButtonEnum, ...]
    ) -> None:
        IdMixin.__init__(self, tab_name)
        self.path = path
        self.buttons: tuple[ButtonEnum, ...] = buttons
        self.operate_dismiss_data: OperateData = OperateData(
            path=self.path, operation_executed=False, tab_name=self.tab_name
        )
        super().__init__(
            id=ModalIdStr.operate_modal, classes=TcssStr.modal_base
        )

    def compose(self) -> ComposeResult:
        with Vertical(
            id=ModalIdStr.operate_vertical, classes=TcssStr.modal_container
        ):
            yield AutoWarning(self.tab_name)
            yield OperateInfo(self.tab_name, self.path)
            if self.tab_name == TabStr.add_tab:
                with Collapsible(
                    id=ModalIdStr.operate_collapsible, title="File Contents"
                ):
                    yield ContentsView(view_id=ModalIdStr.modal_contents_view)

            else:
                with Collapsible(
                    id=ModalIdStr.operate_collapsible, title="File Differences"
                ):
                    yield DiffView(
                        tab_name=self.tab_name,
                        view_id=ModalIdStr.modal_diff_view,
                    )
            yield op_log
            yield ButtonsHorizontal(
                self.tab_name, buttons=self.buttons, location=Location.bottom
            )

    def on_mount(self) -> None:
        if (
            self.tab_name == TabStr.apply_tab
            or self.tab_name == TabStr.re_add_tab
        ):
            # Set path for the modal diff view
            self.query_one(ModalIdStr.modal_diff_view.qid, DiffView).path = (
                self.path
            )
        elif self.tab_name == TabStr.add_tab:
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
        if self.buttons[0] == ButtonEnum.forget_file_btn:
            command += OperateVerbs.forget.value
        elif self.buttons[0] == ButtonEnum.destroy_file_btn:
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
        button_actions = [
            (ButtonEnum.apply_file_btn, chezmoi.perform.apply),
            (ButtonEnum.re_add_file_btn, chezmoi.perform.re_add),
            (ButtonEnum.add_file_btn, chezmoi.perform.add),
            (ButtonEnum.forget_file_btn, chezmoi.perform.forget),
            (ButtonEnum.destroy_file_btn, chezmoi.perform.destroy),
        ]
        for btn_enum, action in button_actions:
            if event.button.id == self.button_id(btn_enum):
                self.query_one(
                    self.button_qid(ButtonEnum.operate_dismiss_btn), Button
                ).label = "Close"
                action(self.path)  # run the perform command with the path
                self.query_one(self.button_qid(btn_enum), Button).disabled = (
                    True
                )
                self.operate_dismiss_data.operation_executed = True
                break

        if event.button.id == self.button_id(ButtonEnum.operate_dismiss_btn):
            self.handle_dismiss(self.operate_dismiss_data)

    def handle_dismiss(self, dismiss_data: OperateData) -> None:
        if not dismiss_data.operation_executed:
            msg = f"Operation cancelled for {self.path.name}"
            cmd_log.log_success(msg)
            op_log.log_success(msg)
            self.notify("No changes were made")
        # send the needed data to the app, logging will be handled there
        self.app.post_message(OperateMessage(dismiss_data=dismiss_data))
        self.dismiss()

    def action_esc_dismiss(self) -> None:
        self.handle_dismiss(self.operate_dismiss_data)


class Maximized(ModalScreen[None], IdMixin):
    BINDINGS = [
        Binding(
            key="escape", action="dismiss", description="close", show=False
        )
    ]

    def __init__(
        self,
        id_to_maximize: str | None,
        path: Path | None,
        tab_name: TabStr = TabStr.apply_tab,
    ) -> None:
        IdMixin.__init__(self, tab_name)
        self.id_to_maximize = id_to_maximize
        self.path = path
        super().__init__(
            id=ModalIdStr.maximized_modal.name, classes=TcssStr.modal_base
        )

    def compose(self) -> ComposeResult:
        with Vertical(
            id=ModalIdStr.maximized_vertical, classes=TcssStr.modal_container
        ):
            if self.id_to_maximize == self.view_id(ViewStr.contents_view):
                yield ContentsView(view_id=ModalIdStr.modal_contents_view)
            elif self.id_to_maximize == self.view_id(ViewStr.diff_view):
                yield DiffView(
                    tab_name=self.tab_name, view_id=ModalIdStr.modal_diff_view
                )
            elif self.id_to_maximize == self.view_id(ViewStr.git_log_view):
                yield GitLogView(view_id=ModalIdStr.modal_git_log_view)

    def on_mount(self) -> None:
        self.border_subtitle = " double click or escape key to close "

        if self.id_to_maximize == self.view_id(ViewStr.contents_view):
            self.query_one(
                ModalIdStr.modal_contents_view.qid, ContentsView
            ).path = self.path
        elif self.id_to_maximize == self.view_id(ViewStr.diff_view):
            self.query_one(ModalIdStr.modal_diff_view.qid, DiffView).path = (
                self.path
            )
        elif self.id_to_maximize == self.view_id(ViewStr.git_log_view):
            self.query_one(
                ModalIdStr.modal_git_log_view.qid, GitLogView
            ).path = self.path

        if self.path == CM_CFG.destDir or self.path is None:
            self.border_title_text = f" {CM_CFG.destDir} "
        else:
            self.border_title_text = (
                f" {self.path.relative_to(CM_CFG.destDir)} "
            )
        self.border_title = self.border_title_text

    def on_click(self, event: Click) -> None:
        event.stop()
        if event.chain == 2:
            self.dismiss()
