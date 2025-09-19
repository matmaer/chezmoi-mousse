import json
import os
from importlib.resources import files
from pathlib import Path

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical, VerticalGroup
from textual.events import Click
from textual.screen import Screen
from textual.widgets import Button, Collapsible, Label, Link, Pretty, Tree

from chezmoi_mousse.chezmoi import chezmoi, op_log
from chezmoi_mousse.constants import BorderSubTitle, OperateVerbs, TcssStr
from chezmoi_mousse.containers import ButtonsHorizontal
from chezmoi_mousse.id_typing import (
    AppType,
    Area,
    Id,
    OperateBtn,
    OperateButtons,
    OperateData,
    ParsedJson,
    TabIds,
    TabName,
    ViewName,
)
from chezmoi_mousse.messages import OperateMessage
from chezmoi_mousse.widgets import (
    ContentsView,
    DiffView,
    GitLogView,
    OperateInfo,
)


class ScreensBase(Screen[None], AppType):

    BINDINGS = [
        Binding(
            key="escape", action="esc_dismiss", description="close", show=False
        )
    ]

    def __init__(self, *, screen_id: str) -> None:
        self.screen_id = screen_id
        super().__init__(id=self.screen_id, classes=TcssStr.screen_base)

    def on_click(self, event: Click) -> None:
        event.stop()
        if (
            event.chain == 2
            and self.screen_id == Id.maximized_screen.screen_id
        ):
            self.dismiss()

    def action_esc_dismiss(self) -> None:
        if self.screen_id in [
            Id.maximized_screen.screen_id,
            Id.operate_screen.screen_id,
        ]:
            self.dismiss()
        elif self.screen_id == Id.install_help_screen.screen_id:
            self.app.exit()


class Operate(ScreensBase):

    def __init__(
        self, *, tab_ids: TabIds, path: Path, buttons: OperateButtons
    ) -> None:
        self.buttons: OperateButtons = buttons
        self.main_operate_btn = self.buttons[0]
        self.path = path
        self.tab_ids = tab_ids
        self.tab_name = tab_ids.tab_name
        self.reverse: bool = (
            False if self.tab_name == TabName.apply_tab else True
        )
        self.operate_dismiss_data: OperateData = OperateData(
            path=self.path,
            operation_executed=False,
            tab_name=self.tab_ids.tab_name,
        )
        super().__init__(screen_id=Id.operate_screen.screen_id)

    def compose(self) -> ComposeResult:
        yield OperateInfo(operate_btn=self.main_operate_btn, path=self.path)
        if (
            OperateBtn.apply_file == self.main_operate_btn
            or OperateBtn.re_add_file == self.main_operate_btn
        ):
            yield DiffView(ids=Id.operate_screen, reverse=self.reverse)
        else:
            yield ContentsView(ids=Id.operate_screen)
        with VerticalGroup():
            yield ButtonsHorizontal(
                tab_ids=self.tab_ids, buttons=self.buttons, area=Area.bottom
            )
            yield op_log

    def on_mount(self) -> None:
        self.add_class(TcssStr.operate_screen)
        self.border_subtitle = BorderSubTitle.esc_to_close
        if (
            self.tab_name == TabName.apply_tab
            or self.tab_name == TabName.re_add_tab
        ) and (
            OperateBtn.apply_file in self.buttons
            or OperateBtn.re_add_file in self.buttons
        ):
            # Set path for the screen diff view
            self.query_one(
                Id.operate_screen.view_id("#", view=ViewName.diff_view),
                DiffView,
            ).path = self.path
        else:
            # Set path for the screen contents view
            self.query_one(
                Id.operate_screen.view_id("#", view=ViewName.contents_view),
                ContentsView,
            ).path = self.path
        self.write_initial_log_msg()

    def write_initial_log_msg(self) -> None:
        command = "chezmoi "
        if self.buttons[0] == OperateBtn.forget_file:
            command += OperateVerbs.forget
        elif self.buttons[0] == OperateBtn.destroy_file:
            command += OperateVerbs.destroy
        elif self.tab_name == TabName.add_tab:
            command += OperateVerbs.add
        elif self.tab_name == TabName.apply_tab:
            command += OperateVerbs.apply
        elif self.tab_name == TabName.re_add_tab:
            command += OperateVerbs.re_add
        chezmoi.op_log.ready_to_run(
            f"Ready to run command: {command} {self.path}"
        )

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
            if event.button.id == self.tab_ids.button_id(btn=btn_enum):
                self.query_one(
                    self.tab_ids.button_id(
                        "#", btn=OperateBtn.operate_dismiss
                    ),
                    Button,
                ).label = "Close"
                btn_cmd(self.path)  # run the perform command with the path
                self.query_one(
                    self.tab_ids.button_id("#", btn=btn_enum), Button
                ).disabled = True
                self.operate_dismiss_data.operation_executed = True
                break

        if event.button.id == self.tab_ids.button_id(
            btn=OperateBtn.operate_dismiss
        ):
            self.handle_dismiss(self.operate_dismiss_data)

    def action_esc_dismiss(self) -> None:
        self.handle_dismiss(self.operate_dismiss_data)

    def handle_dismiss(self, dismiss_data: OperateData) -> None:
        if not dismiss_data.operation_executed and self.path:
            msg = f"Operation cancelled for {self.path.name}"
            chezmoi.op_log.success(msg)
            self.notify("No changes were made")
        # send the needed data to the app, logging will be handled there
        self.app.post_message(OperateMessage(dismiss_data=dismiss_data))
        self.dismiss()


class Maximized(ScreensBase):

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
        self.tab_name: TabName = tab_ids.tab_name
        self.reverse: bool = (
            False if self.tab_name == TabName.apply_tab else True
        )
        super().__init__(screen_id=Id.maximized_screen.screen_id)

    def compose(self) -> ComposeResult:
        with Vertical():
            if self.id_to_maximize == self.tab_ids.view_id(
                view=ViewName.contents_view
            ):
                yield ContentsView(ids=Id.maximized_screen)
            elif self.id_to_maximize == self.tab_ids.view_id(
                view=ViewName.diff_view
            ):
                yield DiffView(ids=Id.maximized_screen, reverse=self.reverse)
            elif self.id_to_maximize == self.tab_ids.view_id(
                view=ViewName.git_log_view
            ):
                yield GitLogView(ids=Id.maximized_screen)

    def on_mount(self) -> None:
        self.border_subtitle = BorderSubTitle.double_click_esc_to_close
        if self.id_to_maximize == self.tab_ids.view_id(
            view=ViewName.contents_view
        ):
            self.query_one(
                Id.maximized_screen.view_id("#", view=ViewName.contents_view),
                ContentsView,
            ).path = self.path
        elif self.id_to_maximize == self.tab_ids.view_id(
            view=ViewName.diff_view
        ):
            self.query_one(
                Id.maximized_screen.view_id("#", view=ViewName.diff_view),
                DiffView,
            ).path = self.path
        elif self.id_to_maximize == self.tab_ids.view_id(
            view=ViewName.git_log_view
        ):
            self.query_one(
                Id.maximized_screen.view_id("#", view=ViewName.git_log_view),
                GitLogView,
            ).path = self.path

        if self.path == chezmoi.destDir:
            self.border_title = f" {chezmoi.destDir} "
        elif self.path is not None:
            self.border_title = f" {self.path.relative_to(chezmoi.destDir)} "


class InstallHelp(ScreensBase):

    def __init__(self) -> None:
        super().__init__(screen_id=Id.install_help_screen.screen_id)
        self.path_env = os.environ.get("PATH") or ""

    def compose(self) -> ComposeResult:
        with Vertical(classes=TcssStr.install_help):
            yield Center(Label(("Chezmoi is not installed or not found.")))
            if not self.path_env:
                yield Center(Label(("The $PATH variable is empty")))
            else:
                yield Collapsible(
                    Pretty(self.path_env),
                    title="'chezmoi' command not found in any search path",
                )
            with Horizontal():
                with VerticalGroup():
                    yield Tree(label=" Install chezmoi ")
                with VerticalGroup():
                    yield Link(
                        "chezmoi.io/install",
                        url="https://chezmoi.io/install",
                        classes=TcssStr.internet_links,
                    )
                    yield Button("exit app", variant="primary", flat=True)

    def on_mount(self) -> None:
        self.border_subtitle = BorderSubTitle.esc_to_exit_app
        help_tree: Tree[ParsedJson] = self.query_exactly_one(Tree[ParsedJson])
        help_tree.show_root = False
        pkg_root = (
            Path(str(files(__package__)))
            if __package__
            else Path(__file__).resolve().parent
        )
        data_file: Path = pkg_root / "data" / "chezmoi_install_commands.json"
        install_help: ParsedJson = json.loads(data_file.read_text())
        for k, v in install_help.items():
            help_tree.root.add(label=k, data=v)
        for child in help_tree.root.children:
            assert child.data is not None
            install_commands: dict[str, str] = child.data
            for k, v in install_commands.items():
                child_label = Text(k, style="warning")
                new_child = child.add(label=child_label)
                cmd_label = Text(v)
                new_child.add_leaf(label=cmd_label)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.exit()
