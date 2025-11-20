import json
import os
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalGroup
from textual.screen import Screen
from textual.widgets import Button, Collapsible, Pretty, Tree

from chezmoi_mousse import AppType, CanvasName, Chars, FlatBtn, LinkBtn, Tcss
from chezmoi_mousse.shared import FlatButton, FlatLink, SectionLabel

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

type ParsedJson = dict[str, Any]

__all__ = ["InstallHelp"]


class InstallHelpStrings(StrEnum):
    collapsible_title = "'chezmoi' command not found in any search path"
    escape_exit_app = " escape key to exit app "
    exit_app_action = "exit_application"
    install_chezmoi = " Install chezmoi "
    no_path_var = "PATH variable is empty or not set."
    top_label = "Chezmoi is not installed or not found."


class CommandsTree(Tree[ParsedJson]):
    ICON_NODE = Chars.right_triangle
    ICON_NODE_EXPANDED = Chars.down_triangle

    def __init__(self) -> None:
        super().__init__(label=InstallHelpStrings.install_chezmoi)


class InstallHelp(Screen[None], AppType):

    BINDINGS = [
        Binding(
            key="escape", action=InstallHelpStrings.exit_app_action, show=False
        )
    ]

    def __init__(self, *, ids: "AppIds") -> None:
        super().__init__(id=CanvasName.install_help_screen)
        self.ids = ids

    def compose(self) -> ComposeResult:
        yield SectionLabel(InstallHelpStrings.top_label)
        yield Collapsible(
            Pretty(InstallHelpStrings.no_path_var),
            title=InstallHelpStrings.collapsible_title,
            collapsed_symbol=Chars.right_triangle,
            expanded_symbol=Chars.down_triangle,
            collapsed=False,
        )
        with Horizontal():
            yield CommandsTree()
            with VerticalGroup():
                yield FlatLink(ids=self.ids, link_enum=LinkBtn.chezmoi_install)
                yield FlatButton(ids=self.ids, button_enum=FlatBtn.exit_app)

    def on_mount(self) -> None:
        self.add_class(Tcss.install_help.name)
        self.border_subtitle = InstallHelpStrings.escape_exit_app
        self.update_path_widget()
        self.populate_tree()

    def update_path_widget(self) -> None:
        self.path_env = os.environ.get("PATH")
        entry_sep = ";" if os.name == "nt" else ":"
        if self.path_env is not None:
            self.path_env_list = self.path_env.split(entry_sep)
            pretty_widget = self.query_exactly_one(Pretty)
            pretty_widget.update(self.path_env_list)

    def populate_tree(self) -> None:
        help_tree: CommandsTree = self.query_exactly_one(CommandsTree)
        data_file = Path(__file__).parent / "chezmoi_install_commands.json"
        install_help: ParsedJson = json.loads(data_file.read_text())
        help_tree.show_root = False
        for k, v in install_help.items():
            help_tree.root.add(label=k, data=v)
        for child in help_tree.root.children:
            if child.data is None:
                self.app.notify(
                    f"InstallHelp: TreeNode data is None for {child.label}",
                    severity="error",
                )
                continue
            install_commands: dict[str, str] = child.data
            for k, v in install_commands.items():
                child_label = Text(k, style="warning")
                new_child = child.add(label=child_label)
                cmd_label = Text(v)
                new_child.add_leaf(label=cmd_label)

    @on(Button.Pressed)
    def exit_application(self, event: Button.Pressed) -> None:
        self.app.exit()

    def action_exit_application(self) -> None:
        self.app.exit()
