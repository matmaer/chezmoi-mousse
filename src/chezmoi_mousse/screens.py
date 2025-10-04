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

from chezmoi_mousse.button_groups import OperateBtnHorizontal
from chezmoi_mousse.chezmoi import ChangeCmd
from chezmoi_mousse.id_typing import AppType, Id, ParsedJson, TabIds
from chezmoi_mousse.id_typing.enums import OperateBtn, TabName, Tcss, ViewName
from chezmoi_mousse.messages import OperateDismissMsg
from chezmoi_mousse.rich_logs import ContentsView, DiffView
from chezmoi_mousse.widgets import GitLogView, OperateInfo


class ScreensBase(Screen[None], AppType):

    BINDINGS = [
        Binding(
            key="escape", action="esc_dismiss", description="close", show=False
        )
    ]

    def __init__(self, *, screen_id: str) -> None:
        self.screen_id = screen_id
        super().__init__(id=self.screen_id, classes=Tcss.screen_base.name)

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


class Operate(ScreensBase, AppType):

    def __init__(
        self, *, tab_ids: TabIds, path: Path, buttons: tuple[OperateBtn, ...]
    ) -> None:
        self.buttons: tuple[OperateBtn, ...] = buttons
        self.main_operate_btn = self.buttons[0]
        self.path = path
        self.tab_ids = tab_ids
        self.reverse: bool = (
            False if self.tab_ids.tab_name == TabName.apply_tab.name else True
        )
        self.operate_dismiss_msg = OperateDismissMsg(
            path=self.path, operation_executed=False
        )
        super().__init__(screen_id=Id.operate_screen.screen_id)

    def compose(self) -> ComposeResult:
        yield OperateInfo(operate_btn=self.main_operate_btn, path=self.path)
        if (
            OperateBtn.apply_file == self.main_operate_btn
            or OperateBtn.re_add_file == self.main_operate_btn
        ):
            yield DiffView(tab_ids=Id.operate_screen, reverse=self.reverse)
        else:
            yield ContentsView(tab_ids=Id.operate_screen)
            yield OperateBtnHorizontal(
                tab_ids=self.tab_ids, buttons=self.buttons
            )

    def on_mount(self) -> None:
        self.app.notify(f"Path is {self.path}")
        self.add_class(Tcss.operate_screen.name)
        self.border_subtitle = Id.operate_screen.border_subtitle()
        for button in self.query(Button):
            button.disabled = False
        if (
            self.tab_ids.tab_name == TabName.apply_tab.name
            or self.tab_ids.tab_name == TabName.re_add_tab.name
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

    @on(Button.Pressed, Tcss.operate_button.value)
    def handle_operate_buttons(self, event: Button.Pressed) -> None:
        event.stop()
        button_commands = [
            (
                OperateBtn.apply_file,
                lambda: self.app.chezmoi.perform(
                    ChangeCmd.apply, str(self.path)
                ),
            ),
            (
                OperateBtn.re_add_file,
                lambda: self.app.chezmoi.perform(
                    ChangeCmd.re_add, str(self.path)
                ),
            ),
            (
                OperateBtn.add_file,
                lambda: self.app.chezmoi.perform(
                    ChangeCmd.add, str(self.path)
                ),
            ),
            (
                OperateBtn.forget_file,
                lambda: self.app.chezmoi.perform(
                    ChangeCmd.forget, str(self.path)
                ),
            ),
            (
                OperateBtn.destroy_file,
                lambda: self.app.chezmoi.perform(
                    ChangeCmd.destroy, str(self.path)
                ),
            ),
        ]
        for btn_enum, btn_cmd in button_commands:
            if event.button.id == self.tab_ids.button_id(btn=btn_enum):
                self.query_one(
                    self.tab_ids.button_id(
                        "#", btn=OperateBtn.operate_dismiss
                    ),
                    Button,
                ).label = "Close"
                btn_cmd()
                self.query_one(
                    self.tab_ids.button_id("#", btn=btn_enum), Button
                ).disabled = True
                self.operate_dismiss_msg.operation_executed = True
                break

        if event.button.id == self.tab_ids.button_id(
            btn=OperateBtn.operate_dismiss
        ):
            self.handle_dismiss()

    def action_esc_dismiss(self) -> None:
        self.handle_dismiss()

    def handle_dismiss(self) -> None:
        if not self.operate_dismiss_msg.operation_executed and self.path:
            self.notify("No changes were made")
        self.app.post_message(self.operate_dismiss_msg)
        self.dismiss()


class Maximized(ScreensBase):

    def __init__(
        self, *, id_to_maximize: str | None, path: Path | None, tab_ids: TabIds
    ) -> None:
        self.id_to_maximize = id_to_maximize
        self.path = path
        self.tab_ids = tab_ids
        self.reverse: bool = (
            False if self.tab_ids.tab_name == TabName.apply_tab.name else True
        )
        super().__init__(screen_id=Id.maximized_screen.screen_id)

    def compose(self) -> ComposeResult:
        with Vertical():
            if self.id_to_maximize == self.tab_ids.view_id(
                view=ViewName.contents_view
            ):
                yield ContentsView(tab_ids=Id.maximized_screen)
            elif self.id_to_maximize == self.tab_ids.view_id(
                view=ViewName.diff_view
            ):
                yield DiffView(
                    tab_ids=Id.maximized_screen, reverse=self.reverse
                )
            elif self.id_to_maximize == self.tab_ids.view_id(
                view=ViewName.git_log_view
            ):
                yield GitLogView(tab_ids=Id.maximized_screen)

    def on_mount(self) -> None:
        self.add_class(Tcss.border_title_top.name)
        self.border_subtitle = self.border_subtitle = (
            Id.maximized_screen.border_subtitle()
        )
        if self.id_to_maximize == self.tab_ids.view_id(
            view=ViewName.contents_view
        ):
            if self.path is not None:
                self.query_one(
                    Id.maximized_screen.view_id(
                        "#", view=ViewName.contents_view
                    ),
                    ContentsView,
                ).path = self.path
        elif self.id_to_maximize == self.tab_ids.view_id(
            view=ViewName.diff_view
        ):
            if self.path is not None:
                self.query_one(
                    Id.maximized_screen.view_id("#", view=ViewName.diff_view),
                    DiffView,
                ).path = self.path
        elif self.id_to_maximize == self.tab_ids.view_id(
            view=ViewName.git_log_view
        ):
            if self.path is not None:
                self.query_one(
                    Id.maximized_screen.view_id(
                        "#", view=ViewName.git_log_view
                    ),
                    GitLogView,
                ).path = self.path

        if self.path == self.app.destDir:
            self.border_title = f" {self.app.destDir} "
        elif self.path is not None:
            self.border_title = f" {self.path.relative_to(self.app.destDir)} "


class InstallHelp(ScreensBase):

    def __init__(self) -> None:
        super().__init__(screen_id=Id.install_help_screen.screen_id)
        self.path_env = os.environ.get("PATH") or ""

    def compose(self) -> ComposeResult:
        with Vertical(classes=Tcss.install_help.name):
            yield Center(Label(("Chezmoi is not installed or not found.")))
            if not self.path_env:
                yield Center(Label(("The $PATH variable is empty")))
            else:
                yield Collapsible(
                    Pretty(self.path_env),
                    title="'chezmoi' command not found in any search path",
                )

            with Center():
                with Horizontal():
                    yield Tree(label=" Install chezmoi ")
                    with VerticalGroup():
                        yield Link(
                            "chezmoi.io/install",
                            url="https://chezmoi.io/install",
                            classes=Tcss.internet_links.name,
                        )
                        yield Button("exit app", variant="primary", flat=True)

    def on_mount(self) -> None:
        self.border_subtitle = self.border_subtitle = (
            Id.operate_screen.border_subtitle()
        )
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

    @on(Button.Pressed)
    def exit_application(self, event: Button.Pressed) -> None:
        self.app.exit()
