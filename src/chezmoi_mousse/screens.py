from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.events import Click
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Collapsible

from chezmoi_mousse import CM_CFG
from chezmoi_mousse.chezmoi import chezmoi, op_log
from chezmoi_mousse.containers import ButtonsHorizontal
from chezmoi_mousse.id_typing import (
    ButtonEnum,
    CharsEnum,
    IdMixin,
    Location,
    OperateIdStr,
    ScreenStr,
    TabStr,
    TcssStr,
    ViewStr,
)
from chezmoi_mousse.widgets import (
    AutoWarning,
    ContentsView,
    DiffView,
    GitLogView,
    OperateInfo,
    RichLog,
)


class OperationCompleted(Message):
    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__()


class Operate(ModalScreen[Path], IdMixin):
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
        self.buttons = buttons
        self.command_executed = False
        self.diff_id = self.view_id(ViewStr.diff_view, operate=True)
        self.diff_qid = self.view_qid(ViewStr.diff_view, operate=True)
        self.contents_id = self.view_id(ViewStr.contents_view, operate=True)
        self.contents_qid = self.view_qid(ViewStr.contents_view, operate=True)
        self.log_id = OperateIdStr.operate_log_id
        self.log_qid = f"#{self.log_id}"
        super().__init__(id=ScreenStr.operate_modal)

    def compose(self) -> ComposeResult:
        with Vertical(
            id=OperateIdStr.operate_vertical_id,
            classes=TcssStr.operate_container,
        ):
            yield AutoWarning(self.tab_name)
            yield OperateInfo(self.tab_name, self.path)
            if self.tab_name == TabStr.add_tab:
                with Container(
                    id=OperateIdStr.operate_collapsible_id,
                    classes=TcssStr.collapsible_container,
                ):
                    yield Collapsible(
                        ContentsView(view_id=self.contents_id),
                        classes=TcssStr.operate_collapsible,
                        title="file contents view",
                    )
            else:
                with Container(
                    id=OperateIdStr.operate_collapsible_id,
                    classes=TcssStr.collapsible_container,
                ):
                    yield Collapsible(
                        DiffView(tab_name=self.tab_name, view_id=self.diff_id),
                        classes=TcssStr.operate_collapsible,
                        title="file diffs view",
                    )
            yield op_log
            yield ButtonsHorizontal(
                self.tab_name, buttons=self.buttons, location=Location.bottom
            )

    def on_mount(self) -> None:
        log_border_titles = {
            TabStr.apply_tab: str(ButtonEnum.apply_file_btn.value).lower(),
            TabStr.re_add_tab: str(ButtonEnum.re_add_file_btn.value).lower(),
            TabStr.add_tab: str(ButtonEnum.add_file_btn.value).lower(),
        }
        self.query_exactly_one(AutoWarning).add_class(
            TcssStr.operate_auto_warning
        )
        self.query_exactly_one(OperateInfo).add_class(TcssStr.operate_top_path)
        if self.tab_name in (TabStr.apply_tab, TabStr.re_add_tab):
            self.query_exactly_one(DiffView).add_class(TcssStr.operate_diff)

        # Add initial log entry
        self.query_one(self.log_qid, RichLog).border_title = (
            f"{log_border_titles[self.tab_name]} log"
        )
        # Set path for either diff or contents view
        if self.tab_name == TabStr.add_tab:
            self.query_one(self.contents_qid, ContentsView).path = self.path
            op_log.log_warning("--- ready to run chezmoi add ---")
        elif self.tab_name in (TabStr.apply_tab, TabStr.re_add_tab):
            self.query_one(self.diff_qid, DiffView).path = self.path
            if self.tab_name == TabStr.apply_tab:
                op_log.log_warning("--- ready to run chezmoi apply ---")
            elif self.tab_name == TabStr.re_add_tab:
                op_log.log_warning("--- ready to run chezmoi re-add ---")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        notify_message = f"Operation completed for {self.path.name}"

        if event.button.id == self.button_id(ButtonEnum.apply_file_btn):
            chezmoi.perform.apply(self.path)
            self.query_one(
                self.button_qid(ButtonEnum.apply_file_btn), Button
            ).disabled = True
            self.query_one(
                self.button_qid(ButtonEnum.cancel_apply_btn), Button
            ).label = "Close"
            self.notify(notify_message)
            self.command_executed = True

        elif event.button.id == self.button_id(ButtonEnum.re_add_file_btn):
            chezmoi.perform.re_add(self.path)
            self.query_one(
                self.button_qid(ButtonEnum.re_add_file_btn), Button
            ).disabled = True
            self.query_one(
                self.button_qid(ButtonEnum.cancel_re_add_btn), Button
            ).label = "Close"
            self.notify(notify_message)
            self.command_executed = True

        elif event.button.id == self.button_id(ButtonEnum.add_file_btn):
            chezmoi.perform.add(self.path)
            self.query_one(
                self.button_qid(ButtonEnum.add_file_btn), Button
            ).disabled = True
            self.query_one(
                self.button_qid(ButtonEnum.cancel_add_btn), Button
            ).label = "Close"
            self.notify(notify_message)
            self.command_executed = True

        elif event.button.id in (
            self.button_id(ButtonEnum.cancel_apply_btn),
            self.button_id(ButtonEnum.cancel_re_add_btn),
            self.button_id(ButtonEnum.cancel_add_btn),
        ):
            self.handle_dismiss()

    def handle_dismiss(self):
        """Called when the screen is dismissed."""
        if not self.command_executed:
            op_log.log_dimmed(f"Operation cancelled for {self.path.name}")
            self.notify("No changes were made")
        self.dismiss(self.path)

    def action_esc_dismiss(self) -> None:
        self.handle_dismiss()


class Maximized(ModalScreen[None], IdMixin):
    BINDINGS = [
        Binding(
            key="escape", action="dismiss", description="close", show=False
        )
    ]

    def __init__(
        self,
        border_title_text: str,
        id_to_maximize: str | None,
        path: Path | None,
        tab_name: TabStr = TabStr.apply_tab,
    ) -> None:
        IdMixin.__init__(self, tab_name)
        self.border_title_text = border_title_text
        self.id_to_maximize = id_to_maximize
        self.path = path
        self.modal_view_id = "modal_view"
        self.modal_view_qid = f"#{self.modal_view_id}"
        super().__init__(id=ScreenStr.maximized_modal)

    def compose(self) -> ComposeResult:
        if self.id_to_maximize == self.view_id(ViewStr.contents_view):
            yield ContentsView(view_id=self.modal_view_id)
        elif self.id_to_maximize == self.view_id(ViewStr.diff_view):
            yield DiffView(tab_name=self.tab_name, view_id=self.modal_view_id)
        elif self.id_to_maximize == self.view_id(ViewStr.git_log_view):
            yield GitLogView(view_id=self.modal_view_id)

    def on_mount(self) -> None:
        self.add_class(TcssStr.modal_view)
        self.border_subtitle = " double click or escape key to close "

        if self.id_to_maximize == self.view_id(ViewStr.contents_view):
            self.query_one(self.modal_view_qid, ContentsView).path = self.path
        elif self.id_to_maximize == self.view_id(ViewStr.diff_view):
            self.query_one(self.modal_view_qid, DiffView).path = self.path
        elif self.id_to_maximize == self.view_id(ViewStr.git_log_view):
            self.query_one(self.modal_view_qid, GitLogView).path = self.path

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
